import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf


def normalizar(audio, sr):
    import pyloudnorm as pyln
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    if not len(audio) or not np.isfinite(audio).all():
        raise ValueError("O modelo produziu áudio vazio ou inválido.")
    if np.max(np.abs(audio)) < 1e-5:
        raise ValueError("O modelo produziu silêncio. Regenere este segmento.")
    if len(audio) > sr * .4:
        loudness = pyln.Meter(sr).integrated_loudness(audio)
        ganho = float(np.clip(-20.0-loudness, -8, 8)) if np.isfinite(loudness) else 0
    else:
        rms = max(float(np.sqrt(np.mean(audio**2))), 1e-6)
        ganho = float(np.clip(-23-20*np.log10(rms), -8, 8))
    audio = audio * 10**(ganho/20)
    peak = float(np.max(np.abs(audio)))
    if peak > .95:
        audio *= .95/peak
    # Bordas suaves de 5 ms evitam cliques sem alterar o tom.
    n = min(int(sr*.005), len(audio)//2)
    if n:
        audio[:n] *= np.linspace(0, 1, n)
        audio[-n:] *= np.linspace(1, 0, n)
    return audio


def montar(pasta, segmentos, velocidade=1.0, nome="narracao"):
    pasta = Path(pasta)
    blocos = []
    sr = None
    for seg in segmentos:
        file = pasta / seg["arquivo"]
        audio, taxa = sf.read(file, dtype="float32", always_2d=True)
        audio = audio.mean(axis=1)
        if sr is not None and taxa != sr:
            raise ValueError("Segmentos com taxas de amostragem diferentes.")
        sr = taxa
        # Conserva 60 ms de ambiente junto à fala, além das pausas explícitas.
        active = np.flatnonzero(np.abs(audio) > .005)
        if len(active):
            audio = audio[max(0, active[0]-int(sr*.06)):active[-1]+int(sr*.06)+1]
        blocos.append(normalizar(audio, sr))
        if seg["pausa"]:
            blocos.append(np.zeros(round(seg["pausa"]*sr), dtype=np.float32))
    if not blocos:
        raise ValueError("Nenhum segmento disponível para unir.")
    joined = np.concatenate(blocos)
    base = pasta / f"{nome}_base.wav"
    final = pasta / f"{nome}.wav"
    sf.write(base, joined, sr, subtype="PCM_16")
    ffmpeg = shutil.which("ffmpeg")
    if abs(velocidade-1) > .001:
        if ffmpeg:
            subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(base),
                            "-af", f"atempo={velocidade:.4f}", "-c:a", "pcm_s16le", str(final)],
                           check=True, capture_output=True, timeout=180, creationflags=0x08000000)
        else:
            import librosa
            stretched = librosa.effects.time_stretch(joined, rate=velocidade)
            sf.write(final, stretched, sr, subtype="PCM_16")
    else:
        shutil.copyfile(base, final)
    mp3 = None
    aviso = None
    if ffmpeg:
        mp3 = pasta / f"{nome}.mp3"
        try:
            subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(final),
                            "-c:a", "libmp3lame", "-q:a", "2", str(mp3)],
                           check=True, capture_output=True, timeout=180, creationflags=0x08000000)
        except (subprocess.SubprocessError, OSError) as exc:
            aviso = f"O WAV foi salvo, mas a exportação MP3 falhou: {exc}"
            mp3 = None
    return {"wav": final.name, "mp3": mp3.name if mp3 else None,
            "duracao_s": sf.info(final).duration, "aviso": aviso}
