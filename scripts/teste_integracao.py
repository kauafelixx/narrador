"""Testes reais e sequenciais na GPU. Não é executado ao iniciar a interface."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from narrador.paths import configure, ROOT, OUTPUTS, LOGS
configure(offline=True)

import hashlib
import json
import os
import time
from narrador.controller import Controlador, validar_parametros, referencias
from narrador.texto import ESTILOS


def hashfile(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def acompanhar(generator):
    ultima = None
    final = None
    for data in generator:
        final = data
        mensagem = data.get("mensagem")
        if mensagem != ultima:
            print(mensagem, flush=True)
            ultima = mensagem
    assert final["status"] == "concluido", final
    return final


def main():
    os.environ["NARRADOR_TEST_BLOCK_NETWORK"] = "1"
    controller = Controlador()
    estilo = ESTILOS["Narrador natural"]
    params = validar_parametros("Narrador natural", estilo.expressividade,
                                estilo.temperatura, estilo.cfg, 1, 12345)
    referencia = next(iter(referencias()))
    texto = ("No ano de 1830, uma nova história começou.\n\n"
             "Em 28/10/2026, ela perguntou: será que conseguimos? "
             "Sim, conseguimos!")
    inicio = time.monotonic()
    generator = controller.gerar(texto, referencia, None, True, params)
    first = next(generator)
    try:
        next(controller.gerar("Outra geração.", None, None, True, params))
        raise AssertionError("A geração simultânea não foi bloqueada.")
    except ValueError as exc:
        assert "andamento" in str(exc)
    final = acompanhar(generator)
    folder = OUTPUTS / final["id"]
    assert final.get("rede_bloqueada_teste")
    assert len(final["segmentos"]) == 3
    assert final["resultado"]["mp3"]
    assert "wav" not in final["resultado"]
    assert not list(folder.glob("narracao*.wav"))
    assert "mil oitocentos e trinta" in final["segmentos"][0]["texto_fala"]
    assert "vinte e oito de outubro de dois mil e vinte e seis" in final["segmentos"][1]["texto_fala"]
    assert final["segmentos"][1]["texto_fala"].endswith("?")
    assert final["segmentos"][2]["texto_fala"].endswith("!")
    original = [(s["arquivo"], hashfile(folder / s["arquivo"])) for s in final["segmentos"]]
    params2 = dict(params, temperatura=.75, semente=22222)
    regen = acompanhar(controller.gerar(None, None, None, True, params2, final["id"], 1))
    assert regen["segmentos"][1]["arquivo"] != original[1][0]
    for i in (0, 2):
        assert regen["segmentos"][i]["arquivo"] == original[i][0]
        assert hashfile(folder / regen["segmentos"][i]["arquivo"]) == original[i][1]
    assert (folder / original[1][0]).exists(), "Take anterior não foi preservado"
    # Cancela durante o segundo segmento e verifica a preservação do primeiro.
    cancelado = None
    for data in controller.gerar(texto, referencia, None, True, params):
        if data.get("status") == "gerando" and data.get("atual") == 2:
            controller.cancelar()
        cancelado = data
    assert cancelado["status"] == "cancelado", cancelado
    assert cancelado["segmentos"][0]["arquivo"]
    assert controller.process is None
    assert not controller.lock.locked()
    report = {"referencia": referencia + " (até 10 segundos)", "segmentos": 3,
              "job": final["id"], "cancelado_job": cancelado["id"],
              "rede_bloqueada": True, "exportacao_apenas_mp3": True, "velocidade": 1,
              "datas_anos_por_extenso": True, "pontuacao_preservada": True,
              "regeneracao_segmento_preservou_outros": True,
              "cancelamento_preservou_primeiro_segmento": True,
              "bloqueio_geracoes_simultaneas": True,
              "tempo_total_s": round(time.monotonic()-inicio, 1),
              "resultado": regen["resultado"], "vram_pico_gb": regen.get("vram_pico_gb")}
    (LOGS / "teste_integracao.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
