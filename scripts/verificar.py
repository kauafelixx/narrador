import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from narrador.paths import configure, ROOT, MODEL_CONFIG, MODEL_FILES, LOGS
configure(offline=True)

import hashlib
import importlib.util
import json
import shutil


def main():
    try:
        if sys.version_info[:2] != (3, 11):
            raise RuntimeError("Use o Python 3.11 do ambiente .venv deste projeto.")
        for name in ("torch", "torchaudio", "chatterbox", "gradio", "soundfile", "psutil", "pyloudnorm"):
            if importlib.util.find_spec(name) is None:
                raise RuntimeError(f"Falta a biblioteca {name}. Consulte a seção Instalação do README.md.")
        import torch
        import torchaudio
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA indisponível. Confira o driver NVIDIA e o PyTorch CUDA na .venv.")
        if not MODEL_CONFIG.exists():
            raise RuntimeError("Modelo não preparado. Execute .venv\\Scripts\\python.exe scripts\\baixar_modelo.py uma vez, com internet.")
        config = json.loads(MODEL_CONFIG.read_text(encoding="utf-8"))
        for recurso in (ROOT / ".cache" / "pkuseg" / "spacy_ontonotes" / "features.msgpack",
                        ROOT / ".cache" / "pkuseg" / "spacy_ontonotes" / "weights.npz"):
            if not recurso.exists():
                raise RuntimeError(f"Recurso auxiliar não preparado: {recurso.name}. Execute scripts/baixar_modelo.py uma vez.")
        directory = Path(config["directory"])
        for name in MODEL_FILES:
            file = directory / name
            if not file.is_file() or file.stat().st_size != config["files"][name]["bytes"]:
                raise RuntimeError(f"Arquivo do modelo ausente ou incompleto: {name}. Execute o download explícito novamente.")
            if "--hashes" in sys.argv:
                digest = hashlib.sha256()
                with file.open("rb") as stream:
                    for block in iter(lambda: stream.read(8*1024*1024), b""):
                        digest.update(block)
                if digest.hexdigest() != config["files"][name]["sha256"]:
                    raise RuntimeError(f"Hash incorreto: {name}. Não carregue este arquivo.")
        for nome, metadata in config.get("auxiliares", {}).items():
            file = Path(nome)
            if not file.is_file() or file.stat().st_size != metadata["bytes"]:
                raise RuntimeError(f"Recurso auxiliar ausente ou incompleto: {file.name}.")
            if "--hashes" in sys.argv and hashlib.sha256(file.read_bytes()).hexdigest() != metadata["sha256"]:
                raise RuntimeError(f"Hash incorreto no recurso auxiliar: {file.name}.")
        result = {"python": sys.version.split()[0], "torch": torch.__version__,
                  "torchaudio": torchaudio.__version__, "cuda": torch.version.cuda,
                  "cuda_disponivel": True, "gpu": torch.cuda.get_device_name(0),
                  "vram_gb": round(torch.cuda.get_device_properties(0).total_memory/1024**3, 2),
                  "ffmpeg": shutil.which("ffmpeg"), "modelo": config["repo"],
                  "revisao": config["revision"], "hashes_verificados": "--hashes" in sys.argv}
        (LOGS / "ambiente.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Componentes OK. {result['gpu']} | PyTorch {result['torch']} | CUDA {result['cuda']}.")
        print("Modelo local V3 pronto. Nenhuma instalação ou download será feito ao iniciar.")
        if not result["ffmpeg"]:
            print("FFmpeg não encontrado: o WAV funciona; o MP3 ficará indisponível.")
        return 0
    except Exception as exc:
        print(f"Não foi possível iniciar: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

