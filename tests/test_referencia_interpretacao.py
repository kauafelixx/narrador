import ast
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from narrador.interpretacao import parametros_trecho, texto_para_modelo
from narrador.paths import ROOT
from narrador.referencia import preparar_referencia


class ReferenciaTests(unittest.TestCase):
    def test_silencio_inicial_e_estereo_em_oposicao(self):
        sr = 24000
        fala = .1 * np.sin(2 * np.pi * 220 * np.arange(sr * 12) / sr)
        audio = np.concatenate([np.zeros(sr * 2), fala])
        with tempfile.TemporaryDirectory() as pasta:
            origem = Path(pasta) / "origem.wav"
            destino = Path(pasta) / "referencia.flac"
            sf.write(origem, np.column_stack([audio, -audio]), sr, subtype="FLOAT")
            detalhes = preparar_referencia(origem, destino)
            preparado, taxa = sf.read(destino)
            self.assertEqual(taxa, sr)
            self.assertEqual(preparado.ndim, 1)
            self.assertGreater(detalhes["inicio_s"], 1.8)
            self.assertAlmostEqual(detalhes["duracao_s"], 10, places=2)
            self.assertGreater(np.max(np.abs(preparado)), .1)
            self.assertLessEqual(np.max(np.abs(preparado)), .951)

    def test_rejeita_silencio_e_referencia_curta(self):
        with tempfile.TemporaryDirectory() as pasta:
            origem = Path(pasta) / "origem.wav"
            destino = Path(pasta) / "referencia.flac"
            for segundos in (1, 5):
                sf.write(origem, np.zeros(24000 * segundos), 24000)
                with self.assertRaises(ValueError):
                    preparar_referencia(origem, destino)
            self.assertFalse(destino.exists())


class InterpretacaoTests(unittest.TestCase):
    def test_pergunta_com_aspas_sobrevive_normalizacao_do_motor_instalado(self):
        # Exercita a função oficial sem importar/carregar o modelo de GPU.
        source = ROOT / "chatterbox/src/chatterbox/mtl_tts.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        func = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "punc_norm")
        namespace = {}
        exec(compile(ast.Module(body=[func], type_ignores=[]), str(source), "exec"), namespace)
        for original, final in [('“Você chegou?”', '?'), ('(Sim!)', '!'), ('"É possível?!"', '?!')]:
            preparado = texto_para_modelo(original)
            self.assertTrue(namespace["punc_norm"](preparado).endswith(final))
            self.assertEqual(sorted(original), sorted(preparado))

    def test_pontuacao_e_aspas_controlam_intensidade_sem_mudar_voz(self):
        base = {"expressividade": .6, "temperatura": .75, "cfg": .35}
        neutro = parametros_trecho("Ele chegou.", base)
        pergunta = parametros_trecho('“Ele chegou?”', base)
        exclamacao = parametros_trecho("Ele chegou!", base)
        self.assertLess(neutro["exaggeration"], pergunta["exaggeration"])
        self.assertLess(pergunta["exaggeration"], exclamacao["exaggeration"])
        self.assertEqual(pergunta["cfg_weight"], neutro["cfg_weight"])
        self.assertEqual(base["expressividade"], .6)
        self.assertEqual(parametros_trecho("Sim!", dict(base, expressividade=1.5))["exaggeration"], 1.5)


if __name__ == "__main__":
    unittest.main()
