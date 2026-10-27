import json
import os
from pathlib import Path

from .paths import OUTPUTS


def salvar_json(path, data):
    path = Path(path)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def ler_job(job_id):
    if not job_id or Path(job_id).name != job_id or "/" in job_id or "\\" in job_id:
        raise ValueError("Selecione uma geração do histórico.")
    path = (OUTPUTS / job_id / "projeto.json").resolve()
    if OUTPUTS.resolve() not in path.parents or not path.is_file():
        raise ValueError("Geração não encontrada.")
    return json.loads(path.read_text(encoding="utf-8"))


def historico():
    rows = []
    for file in sorted(OUTPUTS.glob("*/projeto.json"), reverse=True):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            rows.append((f"{data['criado']} · {data['titulo']} · {data['status']}", data["id"]))
        except (OSError, ValueError, KeyError):
            continue
    return rows

