import atexit
import json
import random
import shutil
import subprocess
import sys
import threading
import time
import uuid
import psutil
from datetime import datetime
from pathlib import Path

from .paths import ROOT, OUTPUTS, LOGS
from .storage import ler_job, salvar_json
from .texto import ESTILOS, segmentar


def referencias():
    path = ROOT / "references" / "catalogo.json"
    if not path.exists():
        return {}
    return {item["nome"]: ROOT / item["arquivo"] for item in json.loads(path.read_text(encoding="utf-8-sig"))}


def validar_parametros(estilo, expressividade, temperatura, cfg, velocidade, semente):
    if estilo not in ESTILOS:
        raise ValueError("Estilo desconhecido.")
    for nome, valor, minimo, maximo in (
        ("expressividade", expressividade, .25, 1.5), ("temperatura", temperatura, .1, 1.5),
        ("CFG", cfg, 0, 1), ("velocidade", velocidade, .75, 1.5)):
        if not minimo <= float(valor) <= maximo:
            raise ValueError(f"O controle {nome} está fora do intervalo permitido.")
    semente = int(semente)
    if not 0 <= semente <= 2**32-1:
        raise ValueError("A semente deve estar entre 0 e 4.294.967.295.")
    return dict(estilo=estilo, expressividade=float(expressividade), temperatura=float(temperatura),
                cfg=float(cfg), velocidade=float(velocidade), semente=semente or random.randrange(1, 2**31))


class Controlador:
    def __init__(self):
        self.lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.cancelado = threading.Event()
        self.process = None
        self.job_id = None
        atexit.register(self.cancelar)

    @staticmethod
    def _encerrar_processo(proc):
        # O Python da .venv no Windows pode iniciar outro python.exe real.
        # Encerra apenas a árvore desta tarefa, incluindo esse filho e FFmpeg.
        try:
            raiz = psutil.Process(proc.pid)
            processos = raiz.children(recursive=True) + [raiz]
        except psutil.NoSuchProcess:
            return
        for processo in reversed(processos):
            try:
                processo.terminate()
            except psutil.NoSuchProcess:
                pass
        _, vivos = psutil.wait_procs(processos, timeout=3)
        for processo in vivos:
            try:
                processo.kill()
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs(vivos, timeout=3)
        proc.wait(timeout=3)

    def cancelar(self):
        with self.state_lock:
            self.cancelado.set()
            proc = self.process
        if proc and proc.poll() is None:
            self._encerrar_processo(proc)
        return "Cancelamento solicitado. Os segmentos já salvos serão preservados."

    def _referencia(self, pasta, nome, upload, consentimento):
        referencia = upload or referencias().get(nome)
        if not referencia:
            return None
        if not consentimento:
            raise ValueError("Confirme que o áudio é seu ou que você tem autorização para usá-lo.")
        import soundfile as sf
        # O componente Gradio recebe uploads locais; nada é enviado à nuvem.
        try:
            info = sf.info(str(referencia))
            if info.duration < 3:
                raise ValueError("Use uma referência com pelo menos 3 segundos de fala limpa.")
            with sf.SoundFile(str(referencia)) as stream:
                wav = stream.read(frames=min(len(stream), int(info.samplerate*10)),
                                  dtype="float32", always_2d=True).mean(axis=1)
            destino = pasta / "referencia.wav"
            sf.write(destino, wav, info.samplerate, subtype="PCM_16")
            return destino.name
        except RuntimeError as exc:
            raise ValueError("Não foi possível ler a referência. Use um arquivo WAV, OGG, FLAC ou MP3 válido.") from exc

    def gerar(self, texto, nome_ref, upload, consentimento, params, job_id=None, segmento=None):
        if not self.lock.acquire(blocking=False):
            raise ValueError("Já existe uma geração em andamento. Aguarde ou cancele a tarefa atual.")
        pasta = None
        data = None
        try:
            self.cancelado.clear()
            if job_id:
                data = ler_job(job_id)
                if segmento is None or not 0 <= int(segmento) < len(data["segmentos"]):
                    raise ValueError("Selecione um segmento válido para regenerar.")
                segmento = int(segmento)
                pasta = OUTPUTS / job_id
                data["parametros"] = params
                # Usa a referência original desse projeto para manter a identidade vocal.
                data["status"] = "aguardando"
            else:
                segmentos = segmentar(texto, params["estilo"])
                job_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
                pasta = OUTPUTS / job_id
                pasta.mkdir(parents=True)
                ref = self._referencia(pasta, nome_ref, upload, consentimento)
                data = {"id": job_id, "criado": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "titulo": " ".join(texto.split())[:70], "texto": texto,
                        "parametros": params, "referencia": ref, "segmentos": segmentos,
                        "modelo": "Chatterbox Multilingual V3", "idioma": "pt", "status": "aguardando"}
            data.update(mensagem="Preparando a geração local…", concluidos=0,
                        total_tarefa=1 if segmento is not None else len(data["segmentos"]))
            salvar_json(pasta / "projeto.json", data)
            self.job_id = job_id
            yield data
            cmd = [sys.executable, "-u", "-m", "narrador.worker", job_id]
            if segmento is not None:
                cmd += ["--segmento", str(segmento)]
            inicio = time.monotonic()
            last_message = ""
            ultima_mudanca = inicio
            with (LOGS / f"{job_id}.log").open("a", encoding="utf-8") as log:
                with self.state_lock:
                    if not self.cancelado.is_set():
                        self.process = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=log,
                                                        creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        self.process = None
                proc = self.process
                while proc and proc.poll() is None:
                    self.cancelado.wait(.5)
                    atual = ler_job(job_id)
                    if atual.get("mensagem") != last_message:
                        last_message = atual.get("mensagem")
                        ultima_mudanca = time.monotonic()
                    if time.monotonic()-ultima_mudanca > 600:
                        self.cancelar()
                        atual.update(status="erro", mensagem="O segmento excedeu 10 minutos de processamento. "
                                     "A tarefa foi interrompida; tente um trecho menor.")
                        salvar_json(pasta / "projeto.json", atual)
                        break
                    yield atual
                    if self.cancelado.is_set():
                        break
                if proc and proc.poll() is None:
                    self._encerrar_processo(proc)
                atual = ler_job(job_id)
                if self.cancelado.is_set() and atual.get("status") != "erro":
                    atual.update(status="cancelado", mensagem="Geração cancelada. Os segmentos salvos estão no histórico.")
                elif proc and proc.returncode != 0 and atual.get("status") != "erro":
                    atual.update(status="erro", mensagem=f"O processo de geração encerrou inesperadamente. Consulte logs/{job_id}.log.")
                salvar_json(pasta / "projeto.json", atual)
                yield atual
        finally:
            with self.state_lock:
                proc = self.process
                self.process = None
            if proc and proc.poll() is None:
                self._encerrar_processo(proc)
            self.lock.release()


CONTROLADOR = Controlador()
