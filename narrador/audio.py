"""Montagem sem perdas intermediárias e uma única codificação final em MP3."""

import os
import shutil
import subprocess
import uuid
from pathlib import Path

import numpy as np
import soundfile as sf


def encontrar_ffmpeg():
    """Localiza também a instalação WinGet quando o app herdou um PATH antigo."""
    configurado = os.environ.get("NARRADOR_FFMPEG")
    if configurado and Path(configurado).is_file():
        return configurado
    encontrado = shutil.which("ffmpeg")
    if encontrado:
        return encontrado
    local = os.environ.get("LOCALAPPDATA")
    if local:
        winget = Path(local) / "Microsoft" / "WinGet"
        link = winget / "Links" / "ffmpeg.exe"
        if link.is_file():
            return str(link)
        try:
            candidatos = sorted((winget / "Packages").glob(
                "Gyan.FFmpeg_*/ffmpeg*/bin/ffmpeg.exe"))
            if candidatos:
                return str(candidatos[-1])
        except OSError:
            pass
    return None


def _validar_audio(audio):
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    if not len(audio) or not np.isfinite(audio).all():
        raise ValueError("O modelo produziu áudio vazio ou inválido.")
    if np.max(np.abs(audio)) < 1e-5:
        raise ValueError("O modelo produziu silêncio. Regenere este segmento.")
    return audio


def normalizar(audio, sr):
    """Aplica um ganho único, preservando a dinâmica de toda a interpretação."""
    import pyloudnorm as pyln

    audio = _validar_audio(audio)
    if len(audio) > sr * .4:
        loudness = pyln.Meter(sr).integrated_loudness(audio)
        ganho = float(np.clip(-18.0-loudness, -8, 8)) if np.isfinite(loudness) else 0
    else:
        rms = max(float(np.sqrt(np.mean(audio**2))), 1e-6)
        ganho = float(np.clip(-21-20*np.log10(rms), -8, 8))
    audio = audio * 10**(ganho/20)
    peak = float(np.max(np.abs(audio)))
    # Margem de aproximadamente 1 dB para os picos da codificação MP3.
    if peak > .89:
        audio *= .89/peak
    return audio


def _preparar_trecho(audio, sr):
    audio = _validar_audio(audio)
    # Um limiar baixo e 100 ms de margem conservam finais e consoantes fracas.
    limiar = max(.0001, float(np.max(np.abs(audio))) * .0005)
    active = np.flatnonzero(np.abs(audio) > limiar)
    if len(active):
        margem = round(sr * .1)
        audio = audio[max(0, active[0]-margem):active[-1]+margem+1].copy()
    else:
        audio = audio.copy()
    # Só as bordas recebem um fade curto; não há crossfade sobre as palavras.
    n = min(round(sr*.003), len(audio)//2)
    if n:
        audio[:n] *= np.linspace(0, 1, n)
        audio[-n:] *= np.linspace(1, 0, n)
    return audio


def montar(pasta, segmentos, velocidade=1.0, nome="narracao"):
    pasta = Path(pasta)
    if not np.isfinite(velocidade) or not .5 <= velocidade <= 2:
        raise ValueError("A velocidade precisa estar entre 0,5 e 2.")
    ffmpeg = encontrar_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("FFmpeg não encontrado. Ele é necessário para exportar a narração em MP3.")
    blocos = []
    sr = None
    for seg in segmentos:
        audio, taxa = sf.read(pasta / seg["arquivo"], dtype="float32", always_2d=True)
        audio = audio.mean(axis=1)
        if sr is not None and taxa != sr:
            raise ValueError("Segmentos com taxas de amostragem diferentes.")
        sr = taxa
        blocos.append(_preparar_trecho(audio, sr))
        pausa = float(seg.get("pausa", 0))
        if not np.isfinite(pausa) or pausa < 0:
            raise ValueError("A pausa entre segmentos precisa ser um número positivo ou zero.")
        if pausa:
            blocos.append(np.zeros(round(pausa*sr), dtype=np.float32))
    if not blocos:
        raise ValueError("Nenhum segmento disponível para unir.")
    # Nivelar cada frase separadamente apagava contrastes da interpretação.
    joined = normalizar(np.concatenate(blocos), sr)
    final = pasta / f"{nome}.mp3"
    temporario = pasta / f".{nome}_{uuid.uuid4().hex[:8]}.tmp.mp3"
    comando = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
               "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0"]
    if abs(velocidade-1) > .001:
        comando.extend(["-af", f"atempo={velocidade:.6f}"])
    comando.extend(["-map_metadata", "-1", "-c:a", "libmp3lame", "-q:a", "0",
                    "-write_xing", "1", str(temporario)])
    try:
        # Float32 segue direto ao encoder: sem WAV base/final nem segunda conversão.
        subprocess.run(comando, input=joined.astype("<f4", copy=False).tobytes(),
                       check=True, capture_output=True, timeout=180,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        duracao = sf.info(temporario).duration
        os.replace(temporario, final)
    except subprocess.CalledProcessError as exc:
        detalhe = exc.stderr.decode("utf-8", errors="replace").strip()[-600:]
        raise RuntimeError(f"Não foi possível exportar o MP3: {detalhe}") from exc
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise RuntimeError(f"Não foi possível exportar o MP3: {exc}") from exc
    finally:
        temporario.unlink(missing_ok=True)
    return {"mp3": final.name, "duracao_s": duracao, "velocidade": velocidade, "aviso": None}
