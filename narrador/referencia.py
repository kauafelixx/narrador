"""Prepara uma amostra local sem comprimir novamente a voz de referência."""

from pathlib import Path

import numpy as np
import soundfile as sf


def preparar_referencia(origem, destino):
    """Conserva até dez segundos de fala, retirando somente silêncio inicial."""
    try:
        with sf.SoundFile(str(origem)) as stream:
            sr = stream.samplerate
            if len(stream) < 3 * sr:
                raise ValueError("Use uma referência com pelo menos 3 segundos de fala limpa.")
            # A leitura limitada evita carregar uploads longos inteiros na RAM.
            canais = stream.read(frames=30 * sr, dtype="float32", always_2d=True)
    except (RuntimeError, OSError) as exc:
        raise ValueError("Não foi possível ler a referência. Use WAV, OGG, FLAC ou MP3 válido.") from exc
    if not np.isfinite(canais).all():
        raise ValueError("A referência contém amostras inválidas.")
    audio = canais.mean(axis=1)
    energia_canais = np.mean(canais ** 2, axis=0)
    # Evita cancelamento em gravações estéreo com canais em oposição de fase.
    if np.mean(audio ** 2) < .01 * np.max(energia_canais):
        audio = canais[:, int(np.argmax(energia_canais))].copy()
    audio = audio - np.mean(audio)
    janela = max(1, round(sr * .02))
    quadros = len(audio) // janela
    rms = np.sqrt(np.mean(audio[:quadros * janela].reshape(quadros, janela) ** 2, axis=1))
    ativos = np.flatnonzero(rms > max(.001, float(np.max(rms)) * .03))
    if not len(ativos) or np.max(np.abs(audio)) < .005:
        raise ValueError("A referência está silenciosa ou muito baixa. Envie fala limpa e audível.")
    inicio = max(0, int(ativos[0] * janela - sr * .08))
    fim = min(len(audio), inicio + 10 * sr, int((ativos[-1] + 1) * janela + sr * .12))
    audio = audio[inicio:fim]
    if len(audio) < 3 * sr:
        raise ValueError("A referência precisa conter pelo menos 3 segundos de fala após o silêncio inicial.")
    pico = float(np.max(np.abs(audio)))
    # Só ganho constante; sem compressor, gate ou filtro que altere o timbre.
    audio *= min(.95 / pico, 4.0)
    sf.write(Path(destino), audio, sr, subtype="PCM_24")
    return {"inicio_s": round(inicio / sr, 3), "duracao_s": round(len(audio) / sr, 3),
            "taxa_hz": sr, "canais": 1}
