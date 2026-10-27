import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from narrador.paths import configure, OUTPUTS, LOGS, MODEL_CONFIG
configure(offline="--online" not in sys.argv)

import gc
import json
import time
import socket
import torch
import soundfile as sf

if "--bloquear-rede" in sys.argv:
    def blocked(*args, **kwargs):
        raise RuntimeError("Teste offline: tentativa de acesso à rede bloqueada")
    socket.socket.connect = blocked
    socket.create_connection = blocked

from chatterbox.mtl_tts import ChatterboxMultilingualTTS

assert torch.cuda.is_available(), "CUDA indisponível neste ambiente Python."
torch.set_num_threads(4)
torch.cuda.set_per_process_memory_fraction(0.90)
torch.cuda.reset_peak_memory_stats()
start = time.monotonic()
if "--pretrained" in sys.argv:
    model = ChatterboxMultilingualTTS.from_pretrained(device="cuda", t3_model="v3")
else:
    config = json.loads(MODEL_CONFIG.read_text(encoding="utf-8"))
    model = ChatterboxMultilingualTTS.from_local(config["directory"], device="cuda", t3_model="v3")
loaded = time.monotonic()
text = "Em 1830, no coração de Paris, uma jovem religiosa testemunharia um acontecimento que marcaria para sempre a história da Igreja."
torch.manual_seed(42)
with torch.inference_mode():
    audio = model.generate(text, language_id="pt", exaggeration=0.5, temperature=0.8, cfg_weight=0.5)
suffix = "offline" if "--bloquear-rede" in sys.argv else "inicial"
path = OUTPUTS / f"teste_{suffix}.wav"
sf.write(path, audio.squeeze().numpy(), model.sr, subtype="PCM_16")
result = {"gpu": torch.cuda.get_device_name(), "torch": torch.__version__,
          "cuda": torch.version.cuda, "modelo": "Multilingual V3", "idioma": "pt",
          "carregamento_s": loaded-start, "geracao_s": time.monotonic()-loaded,
          "duracao_s": audio.numel()/model.sr, "sample_rate": model.sr,
          "vram_pico_gb": torch.cuda.max_memory_allocated()/1024**3,
          "rede_bloqueada": "--bloquear-rede" in sys.argv, "arquivo": str(path)}
(LOGS / f"teste_{suffix}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
del model, audio
gc.collect()
torch.cuda.empty_cache()
