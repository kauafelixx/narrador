"""Verifica encerramento da árvore de processos e liberação da GPU."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from narrador.paths import configure, LOGS
configure(offline=True)
import json
import os
import time
import psutil
from narrador.controller import Controlador, validar_parametros, referencias

os.environ["NARRADOR_TEST_BLOCK_NETWORK"] = "1"
controller = Controlador()
params = validar_parametros("Narrador natural", .5, .8, .5, 1, 42)
pids = []
inferencia_inicio = None
inicio = time.monotonic()
for data in controller.gerar("Uma história antiga começava naquela noite, quando as ruas de Paris estavam silenciosas e uma jovem caminhava pela cidade.",
                             next(iter(referencias())), None, True, params):
    if data.get("status") == "gerando":
        if inferencia_inicio is None:
            inferencia_inicio = time.monotonic()
        if time.monotonic()-inferencia_inicio >= 2:
            root = psutil.Process(controller.process.pid)
            pids = [root.pid] + [p.pid for p in root.children(recursive=True)]
            controller.cancelar()
assert data["status"] == "cancelado", data
assert pids, "Não foi possível iniciar a inferência real."
assert not any(psutil.pid_exists(pid) for pid in pids), pids
assert controller.process is None
assert not controller.lock.locked()
report = {"job": data["id"], "status": data["status"], "processos_encerrados": pids,
          "nenhum_processo_filho_restante": True, "cancelado_durante_inferencia": True,
          "duracao_teste_s": round(time.monotonic()-inicio, 1)}
(LOGS / "teste_cancelamento.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)

