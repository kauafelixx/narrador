"""Download inicial explícito. Não é executado pelo iniciar.bat."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from narrador.paths import configure, MODEL_CONFIG, MODEL_FILES
configure(offline=False)

import hashlib
import json
from huggingface_hub import snapshot_download, hf_hub_download, HfApi
from spacy_pkuseg.config import config as pkuseg_config
from spacy_pkuseg.download import download_model

repo = "ResembleAI/chatterbox"
revision = HfApi().model_info(repo).sha
print(f"Baixando modelo oficial {repo}, revisão {revision}", flush=True)
directory = Path(snapshot_download(repo_id=repo, revision=revision,
                                  allow_patterns=list(MODEL_FILES), max_workers=2))
# O tokenizador oficial usa cache_dir=ckpt_dir para este dicionário auxiliar.
aux_cangjie = Path(hf_hub_download(repo_id=repo, filename="Cangjie5_TC.json", cache_dir=directory))
# O tokenizador multilíngue inicializa também o segmentador chinês, mesmo para pt.
# Pré-baixa esse recurso oficial para não haver download implícito em uso normal.
download_model(pkuseg_config.model_urls["spacy_ontonotes"], pkuseg_config.pkuseg_home,
               pkuseg_config.model_hash["spacy_ontonotes"], progress=False)
manifest = {}
for name in MODEL_FILES:
    file = directory / name
    digest = hashlib.sha256()
    with file.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    manifest[name] = {"bytes": file.stat().st_size, "sha256": digest.hexdigest()}
config = {"repo": repo, "revision": revision, "t3_model": "v3", "language_id": "pt",
          "directory": str(directory), "files": manifest}
config["auxiliares"] = {}
for file in (aux_cangjie, Path(pkuseg_config.pkuseg_home) / "spacy_ontonotes" / "features.msgpack",
             Path(pkuseg_config.pkuseg_home) / "spacy_ontonotes" / "weights.npz"):
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    config["auxiliares"][str(file)] = {"bytes": file.stat().st_size, "sha256": digest}
MODEL_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Modelo e hashes registrados em {MODEL_CONFIG}", flush=True)

