import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "huggingface"
OUTPUTS = ROOT / "outputs"
LOGS = ROOT / "logs"
MODEL_CONFIG = ROOT / "models" / "modelo.json"
MODEL_FILES = (
    "ve.pt", "t3_mtl23ls_v3.safetensors", "s3gen.pt",
    "grapheme_mtl_merged_expanded_v1.json", "conds.pt", "Cangjie5_TC.json",
)


def configure(offline=True):
    # Somente este processo e seus filhos; nenhuma variável global do Windows.
    os.environ["HF_HOME"] = str(CACHE)
    os.environ["PKUSEG_HOME"] = str(ROOT / ".cache" / "pkuseg")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "120"
    os.environ["HF_HUB_ETAG_TIMEOUT"] = "30"
    if offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    else:
        os.environ.pop("HF_HUB_OFFLINE", None)
        os.environ.pop("TRANSFORMERS_OFFLINE", None)
    for directory in (OUTPUTS, LOGS, MODEL_CONFIG.parent):
        directory.mkdir(parents=True, exist_ok=True)

