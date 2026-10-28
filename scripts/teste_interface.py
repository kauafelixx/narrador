"""Integração HTTP local, sem automação visual do navegador."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from narrador.paths import ROOT, LOGS, OUTPUTS
import json
import uuid
from urllib.request import Request, urlopen
from urllib.parse import quote

BASE = "http://127.0.0.1:7860"
SESSION = "teste-" + uuid.uuid4().hex


def getjson(path):
    with urlopen(BASE+path, timeout=15) as response:
        assert response.status == 200
        return json.load(response)


def evento(config, name, data):
    index = next(d["id"] for d in config["dependencies"] if d["api_name"] == name)
    session = SESSION
    payload = json.dumps({"data": data, "fn_index": index, "session_hash": session}).encode()
    req = Request(BASE+"/gradio_api/queue/join", data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=20) as response:
        event_id = json.load(response)["event_id"]
    with urlopen(BASE+"/gradio_api/queue/data?session_hash="+session, timeout=30) as response:
        for line in response:
            if line.startswith(b"data: "):
                message = json.loads(line[6:])
                if message.get("event_id") == event_id and message.get("msg") == "process_completed":
                    assert message["success"], message
                    return message["output"]["data"]
    raise AssertionError("Evento sem resposta final")


def main():
    config = getjson("/config")
    assert config["analytics_enabled"] is False
    assert not any(d.get("api_visibility") == "public" for d in config["dependencies"])
    labels = [c["props"].get("label") for c in config["components"]]
    assert "Roteiro" in labels and "Segmento para ouvir ou regenerar" in labels
    assert "pt-BR" in config["js"]
    bundle = config["js"].split("import('")[1].split("')")[0]
    with urlopen(BASE+bundle, timeout=15) as response:
        assert response.status == 200
    report = json.loads((LOGS / "teste_integracao.json").read_text(encoding="utf-8"))
    job_id = report["job"]
    loaded = evento(config, "carregar", [job_id])
    # gr.State é omitido na serialização para o navegador; os outros outputs são reais.
    assert "Narração concluída" in loaded[1]
    assert loaded[2]["path"].endswith(".mp3")
    assert loaded[3]["path"].endswith(".mp3")
    assert len(loaded[5]["data"]) == 3
    selected = evento(config, "ouvir_segmento", [None, 1])
    assert selected[0]["path"].endswith(".wav")
    # Confere também a entrega dos arquivos reais pelo servidor local.
    data = json.loads((OUTPUTS/job_id/"projeto.json").read_text(encoding="utf-8"))
    for name in (data["resultado"]["mp3"],):
        path = str(OUTPUTS/job_id/name).replace("\\", "/")
        with urlopen(BASE+"/gradio_api/file="+quote(path, safe="/:"), timeout=15) as response:
            assert response.status == 200
            assert len(response.read(1024)) == 1024
    result = {"http": 200, "componentes": len(config["components"]),
              "carregamento_historico_via_fila": True, "download_mp3": True,
              "analitica_desativada": True, "apis_publicas": False,
              "idioma_pt_br_configurado": True, "verificacao_visual": "não faz parte do teste HTTP"}
    (LOGS/"teste_interface.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
