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
from narrador.audio import montar
from narrador.controller import referencias
from narrador.interpretacao import parametros_trecho, texto_para_modelo
from narrador.referencia import preparar_referencia
from narrador.texto import normalizar_fala, ESTILOS

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
style = ESTILOS["Narrador natural"]
params = {"expressividade": style.expressividade, "temperatura": style.temperatura, "cfg": style.cfg}
suffix = "offline" if "--bloquear-rede" in sys.argv else "inicial"
folder = OUTPUTS / ("diagnostico_" + time.strftime("%Y%m%d-%H%M%S"))
folder.mkdir(parents=True, exist_ok=False)
ref_name, ref_path = next(iter(referencias().items()))
preparar_referencia(ref_path, folder / "referencia.flac")
model.prepare_conditionals(str(folder / "referencia.flac"), exaggeration=style.expressividade)
torch.manual_seed(42)
with torch.inference_mode():
    audio = model.generate(texto_para_modelo(normalizar_fala(text)), language_id="pt", **parametros_trecho(text, params))
sf.write(folder / "segmento_0001.wav", audio.squeeze().numpy(), model.sr, subtype="PCM_24")
export = montar(folder, [{"arquivo": "segmento_0001.wav", "pausa": 0}], nome=f"teste_{suffix}")
path = folder / export["mp3"]
result = {"gpu": torch.cuda.get_device_name(), "torch": torch.__version__,
          "cuda": torch.version.cuda, "modelo": "Multilingual V3", "idioma": "pt",
          "carregamento_s": loaded-start, "geracao_s": time.monotonic()-loaded,
          "duracao_s": audio.numel()/model.sr, "sample_rate": model.sr,
          "vram_pico_gb": torch.cuda.max_memory_allocated()/1024**3,
          "rede_bloqueada": "--bloquear-rede" in sys.argv, "arquivo": str(path), "referencia": ref_name,
          "texto_fala": normalizar_fala(text)}
(LOGS / f"teste_{suffix}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
del model, audio
gc.collect()
torch.cuda.empty_cache()
