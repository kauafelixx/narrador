"""Regressões para a entrada efetivamente enviada à síntese em português."""
import unittest

from narrador.texto import ESTILOS, normalizar_fala, segmentar


class TextoFalaTests(unittest.TestCase):
    def test_anos_por_extenso_preservam_acentos_e_pontuacao(self):
        self.assertEqual(
            normalizar_fala("No ano de 1830, a história começou. Em 2001, tudo mudou! Até 2100?"),
            "No ano de mil oitocentos e trinta, a história começou. Em dois mil e um, tudo mudou! Até dois mil e cem?",
        )
        self.assertEqual(normalizar_fala("Entre 1830 e 1840."), "Entre mil oitocentos e trinta e mil oitocentos e quarenta.")

    def test_datas_validas_em_formatos_numericos_e_escritos(self):
        casos = {
            "Em 28/10/2026.": "Em vinte e oito de outubro de dois mil e vinte e seis.",
            "Chegou em 01-02-2000!": "Chegou em primeiro de fevereiro de dois mil!",
            "Data: 01.02.2024.": "Data: primeiro de fevereiro de dois mil e vinte e quatro.",
            "Foi em 2024-02-29.": "Foi em vinte e nove de fevereiro de dois mil e vinte e quatro.",
            "Em 1º de janeiro de 2001?": "Em primeiro de janeiro de dois mil e um?",
            "Dia 28 de outubro de 2026.": "Dia vinte e oito de outubro de dois mil e vinte e seis.",
        }
        for original, esperado in casos.items():
            with self.subTest(original=original):
                self.assertEqual(normalizar_fala(original), esperado)

    def test_datas_invalidas_e_identificadores_nao_sao_adivinhados(self):
        for texto in (
            "Em 31/02/2026.", "Em 29/02/2025.", "Data: 00.10.2026.",
            "Dia 28 de outubro de 0000.",
            "Versão 1.2.2026; código 1830; telefone 1830-4567; ID 2026-10-28.",
            "Código 28/10/2026; versão em 1830.1; em 1830/1840.",
            "CPF 1830; 1.830,50; 1830; versão 2026.10.28.",
        ):
            with self.subTest(texto=texto):
                self.assertEqual(normalizar_fala(texto), texto)

    def test_roteiro_original_e_fala_normalizada_ficam_separados(self):
        original = "No ano de 1830, ela perguntou: “Você voltará?” Sim! Depois, em 01/02/2024, chegou."
        segmentos = segmentar(original)
        self.assertEqual(" ".join(s["texto"] for s in segmentos), original)
        self.assertEqual(len(segmentos), 3)
        self.assertEqual(segmentos[0]["texto_fala"], "No ano de mil oitocentos e trinta, ela perguntou: “Você voltará?”")
        self.assertEqual(segmentos[0]["pausa"], .32)
        self.assertEqual(segmentos[1]["texto"], "Sim!")
        self.assertEqual(segmentos[1]["pausa"], .28)
        self.assertEqual(segmentos[-1]["pausa"], 0)

    def test_tamanho_limita_tambem_expansao_das_datas(self):
        original = ("A história começou no ano de 1830 e prosseguiu em 28/10/2026, " * 12).strip() + "."
        for estilo, config in ESTILOS.items():
            with self.subTest(estilo=estilo):
                segmentos = segmentar(original, estilo)
                self.assertEqual(" ".join(s["texto"] for s in segmentos), original)
                self.assertTrue(all(len(s["texto_fala"]) <= config.caracteres for s in segmentos))
                self.assertEqual(" ".join(s["texto_fala"] for s in segmentos), normalizar_fala(original))

    def test_corte_nao_reinterpreta_identificador_como_data(self):
        original = ("Uma narrativa extensa continua enquanto se aproxima a próxima linha " * 5 +
                    "código 28/10/2026 continua identificado no arquivo.")
        segmentos = segmentar(original)
        self.assertEqual(" ".join(s["texto_fala"] for s in segmentos), normalizar_fala(original))
        self.assertIn("código 28/10/2026", " ".join(s["texto_fala"] for s in segmentos))

    def test_pontuacao_composta_reticencias_e_aspas(self):
        original = '“Por quê?!” Ela hesitou… Depois sorriu. (Tudo bem!) Fim.'
        segmentos = segmentar(original)
        self.assertEqual([s["texto"] for s in segmentos],
                         ['“Por quê?!”', 'Ela hesitou…', 'Depois sorriu.', '(Tudo bem!)', 'Fim.'])
        self.assertGreater(segmentos[1]["pausa"], segmentos[2]["pausa"])
        self.assertEqual(" ".join(s["texto"] for s in segmentos), original)


if __name__ == "__main__":
    unittest.main()
