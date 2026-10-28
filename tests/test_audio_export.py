import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

from narrador.audio import montar, normalizar


class ExportacaoAudioTests(unittest.TestCase):
    def test_mp3_conserva_contraste_e_finais_fracos(self):
        with tempfile.TemporaryDirectory() as folder:
            pasta = Path(folder)
            sr = 24000
            t = np.arange(sr) / sr
            fala = .2 * np.sin(2*np.pi*330*t)
            # Finais fracos de 120 ms não devem desaparecer no corte de silêncio.
            fraco = .001 * np.sin(2*np.pi*1200*np.arange(round(.12*sr))/sr)
            trecho = np.concatenate([np.zeros(round(.2*sr)), fraco, fala, fraco,
                                     np.zeros(round(.2*sr))])
            sf.write(pasta / "forte.wav", trecho, sr, subtype="PCM_24")
            sf.write(pasta / "suave.wav", trecho * .5, sr, subtype="PCM_24")
            resultado = montar(pasta, [{"arquivo": "forte.wav", "pausa": .2},
                                       {"arquivo": "suave.wav", "pausa": 0}])
            audio, _ = sf.read(pasta / resultado["mp3"])
            # 0,1 s de margem + 0,12 s fraco + 1 s fala + 0,12 s fraco + 0,1 s.
            self.assertAlmostEqual(resultado["duracao_s"], 3.08, delta=.04)
            a = np.sqrt(np.mean(audio[round(.4*sr):round(.9*sr)] ** 2))
            b = np.sqrt(np.mean(audio[round(2.04*sr):round(2.54*sr)] ** 2))
            self.assertAlmostEqual(a/b, 2, delta=.08)
            self.assertGreater(np.sqrt(np.mean(audio[round(.12*sr):round(.2*sr)]**2)), .0001)
            self.assertLess(np.max(np.abs(audio)), .98)
            self.assertFalse(list(pasta.glob("*.tmp.mp3")))
            self.assertFalse(list(pasta.glob("narracao*.wav")))

    def test_falha_encoder_limpa_temporario_e_preserva_takes(self):
        with tempfile.TemporaryDirectory() as folder:
            pasta = Path(folder)
            sr = 24000
            sf.write(pasta / "take.wav", np.sin(np.arange(sr)*.1)*.1, sr)

            def falhar(comando, **kwargs):
                Path(comando[-1]).write_bytes(b"incompleto")
                raise subprocess.CalledProcessError(1, comando, stderr=b"falha simulada")

            with patch("narrador.audio.encontrar_ffmpeg", return_value="ffmpeg"), \
                    patch("narrador.audio.subprocess.run", side_effect=falhar):
                with self.assertRaisesRegex(RuntimeError, "falha simulada"):
                    montar(pasta, [{"arquivo": "take.wav", "pausa": 0}])
            self.assertEqual([p.name for p in pasta.iterdir()], ["take.wav"])

    def test_sem_ffmpeg_informa_dependencia_sem_criar_arquivos(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch("narrador.audio.encontrar_ffmpeg", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "FFmpeg.*MP3"):
                    montar(folder, [])
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_audio_invalido_e_picos(self):
        for invalido in ([], [0]*24000, [np.nan], [np.inf]):
            with self.assertRaises(ValueError):
                normalizar(invalido, 24000)
        forte = np.sin(np.arange(24000)*.1)*2
        self.assertLessEqual(float(np.max(np.abs(normalizar(forte, 24000)))), .89001)


if __name__ == "__main__":
    unittest.main()
