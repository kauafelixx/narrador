"""Um processo de GPU por tarefa. Encerrá-lo cancela e devolve a VRAM ao SO."""
import argparse
import gc
import json
import os
import time
import traceback
import uuid
from pathlib import Path

from .paths import configure, MODEL_CONFIG, OUTPUTS
from .storage import ler_job, salvar_json


def executar(job_id, selecionado=None, bloquear_rede=False):
    configure(offline=True)
    if bloquear_rede or os.environ.get("NARRADOR_TEST_BLOCK_NETWORK") == "1":
        import socket
        def blocked(*args, **kwargs):
            raise RuntimeError("Teste offline: acesso à rede bloqueado")
        socket.socket.connect = blocked
        socket.create_connection = blocked
    import torch
    import soundfile as sf
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    from .audio import montar
    from .interpretacao import parametros_trecho, texto_para_modelo
    from .texto import normalizar_fala

    pasta = OUTPUTS / job_id
    path = pasta / "projeto.json"
    data = ler_job(job_id)
    inicio = time.monotonic()
    model = None

    def update(mensagem, **extra):
        data.update(extra)
        data["mensagem"] = mensagem
        data["tempo_s"] = round(time.monotonic()-inicio, 1)
        salvar_json(path, data)

    try:
        if not torch.cuda.is_available():
            raise RuntimeError("A GPU NVIDIA não está disponível. Verifique o driver e o PyTorch CUDA.")
        torch.set_num_threads(4)
        # A RTX 3050 (Ampere) pode acelerar multiplicações FP32 com TF32.
        torch.set_float32_matmul_precision("high")
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.cuda.set_per_process_memory_fraction(.90)
        torch.cuda.reset_peak_memory_stats()
        update("Carregando o Multilingual V3 na GPU…", status="carregando", rede_bloqueada_teste=bool(bloquear_rede or os.environ.get("NARRADOR_TEST_BLOCK_NETWORK") == "1"))
        config = json.loads(MODEL_CONFIG.read_text(encoding="utf-8"))
        model = ChatterboxMultilingualTTS.from_local(config["directory"], device="cuda", t3_model="v3")
        params = data["parametros"]
        referencia = str(pasta / data["referencia"]) if data.get("referencia") else None
        if referencia:
            model.prepare_conditionals(referencia, exaggeration=params["expressividade"])
        indices = [selecionado] if selecionado is not None else list(range(len(data["segmentos"])))
        for andamento, i in enumerate(indices):
            seg = data["segmentos"][i]
            update(f"Gerando segmento {i+1} de {len(data['segmentos'])}…",
                   status="gerando", atual=i+1, concluidos=andamento, total_tarefa=len(indices))
            torch.manual_seed((params["semente"]+i) % (2**32))
            trecho_inicio = time.monotonic()
            texto_fala = normalizar_fala(seg["texto"])
            texto_modelo = texto_para_modelo(texto_fala)
            interpretacao = parametros_trecho(texto_fala, params)
            with torch.inference_mode():
                wav = model.generate(texto_modelo, language_id="pt", **interpretacao)
            # Um take novo preserva o anterior em caso de cancelamento/regeneração.
            nome = f"segmento_{i+1:04d}_{uuid.uuid4().hex[:8]}.wav"
            sf.write(pasta / nome, wav.squeeze().numpy(), model.sr, subtype="PCM_24")
            if seg.get("arquivo"):
                seg.setdefault("takes_anteriores", []).append(seg["arquivo"])
            seg.update(arquivo=nome, duracao_s=wav.numel()/model.sr,
                       geracao_s=round(time.monotonic()-trecho_inicio, 2), parametros=dict(params),
                       texto_fala=texto_fala, texto_modelo=texto_modelo, interpretacao=interpretacao)
            del wav
            gc.collect()
            torch.cuda.empty_cache()
            update(f"Segmento {i+1} salvo.", concluidos=andamento+1,
                   vram_pico_gb=round(torch.cuda.max_memory_allocated()/1024**3, 3))
        update("Unindo os segmentos e exportando MP3…", status="exportando")
        completo = all(s.get("arquivo") for s in data["segmentos"])
        if completo:
            final = montar(pasta, data["segmentos"], params["velocidade"],
                           nome=f"narracao_{uuid.uuid4().hex[:8]}")
            data["resultado"] = final
            update("Narração concluída. Arquivos salvos no histórico local.", status="concluido")
        else:
            update("Segmento salvo. Gere os trechos restantes para exportar a narração completa.", status="parcial")
    except torch.cuda.OutOfMemoryError:
        update("Memória da GPU insuficiente. Feche outros aplicativos que usam a GPU e tente um trecho menor. "
               "Os segmentos já salvos foram preservados.", status="erro")
        traceback.print_exc()
        return 2
    except Exception as exc:
        update(f"Não foi possível concluir: {exc}", status="erro")
        traceback.print_exc()
        return 1
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("job")
    parser.add_argument("--segmento", type=int)
    parser.add_argument("--bloquear-rede", action="store_true")
    args = parser.parse_args()
    raise SystemExit(executar(args.job, args.segmento, args.bloquear_rede))
