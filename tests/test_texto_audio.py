import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from narrador.texto import segmentar, ESTILOS
from narrador.audio import montar


class TextoAudioTests(unittest.TestCase):
    def test_preserva_roteiro_abreviacoes_e_paragrafos(self):
        texto = 'O Pe. João chegou em 1830. Ele disse: “Tudo bem!”\n\nA história continuou no cap. 2.'
        segmentos = segmentar(texto)
        self.assertEqual(" ".join(texto.split()), " ".join(s["texto"] for s in segmentos))
        self.assertGreater(segmentos[1]["pausa"], segmentos[0]["pausa"])
        self.assertEqual(segmentos[-1]["pausa"], 0)
        self.assertIn("Pe. João", segmentos[0]["texto"])

    def test_roteiro_de_dez_minutos_sem_perda_e_com_limite(self):
        texto = ("Em Paris, a história começava com uma jovem que caminhava em silêncio pela cidade. " * 100).strip()
        self.assertGreaterEqual(len(texto.split()), 1400)
        for estilo, config in ESTILOS.items():
            segmentos = segmentar(texto, estilo)
            self.assertEqual(texto, " ".join(s["texto"] for s in segmentos))
            self.assertTrue(all(len(s["texto"]) <= config.caracteres for s in segmentos))
            self.assertGreater(len(segmentos), 50)

    def test_frase_longa_preserva_palavras(self):
        texto = ("uma narrativa muito longa, " * 40).strip() + "."
        segmentos = segmentar(texto)
        self.assertGreater(len(segmentos), 2)
        self.assertEqual(texto, " ".join(s["texto"] for s in segmentos))

    def test_limites(self):
        with self.assertRaises(ValueError):
            segmentar("")
        with self.assertRaises(ValueError):
            segmentar("palavra " * 2001)

    def test_uniao_velocidade_preserva_tom_e_mp3(self):
        # Tom conhecido: compara duração e frequência após atempo=1.1.
        with tempfile.TemporaryDirectory() as folder:
            pasta = Path(folder)
            sr = 24000
            audio = .1*np.sin(2*np.pi*220*np.arange(sr*2)/sr)
            sf.write(pasta / "a.wav", audio, sr)
            sf.write(pasta / "b.wav", audio*.5, sr)
            segs = [{"arquivo": "a.wav", "pausa": .3}, {"arquivo": "b.wav", "pausa": 0}]
            normal = montar(pasta, segs, 1, "normal")
            fast = montar(pasta, segs, 1.1, "rapido")
            self.assertAlmostEqual(normal["duracao_s"]/fast["duracao_s"], 1.1, delta=.03)
            y, _ = sf.read(pasta / fast["wav"])
            spectrum = np.abs(np.fft.rfft(y[:sr]))
            frequency = np.argmax(spectrum)
            self.assertAlmostEqual(frequency, 220, delta=3)
            self.assertLessEqual(np.max(np.abs(y)), .96)
            if __import__("shutil").which("ffmpeg"):
                self.assertTrue((pasta / fast["mp3"]).is_file())


if __name__ == "__main__":
    unittest.main()
