import unittest
from copy import deepcopy
from unittest.mock import Mock, patch

from narrador.paths import configure

configure(offline=True)

import gradio as gr

from narrador.interface.actions import getNarrationState, getStatusMessage, streamNarrationState
from narrador.interface.view import buildInterface
from narrador.texto import ESTILOS


class InterfaceStateTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "id": "teste", "status": "gerando", "mensagem": "Gerando segmento 1…",
            "concluidos": 0, "total_tarefa": 2,
            "parametros": {"velocidade": 1},
            "segmentos": [
                {"numero": 1, "texto": "Que história incrível!"},
                {"numero": 2, "texto": "Você consegue imaginar?"},
            ],
        }

    @patch("narrador.interface.actions.getHistory", return_value=[("Teste", "teste")])
    def test_polling_identico_nao_recria_controles_nem_reenvia_dados(self, history):
        snapshots = [deepcopy(self.data) for _ in range(8)]
        for index, snapshot in enumerate(snapshots):
            snapshot["tempo_s"] = index / 2
        progress = Mock()
        updates = list(streamNarrationState(snapshots, progress))
        self.assertEqual(len(updates), 1)
        self.assertEqual(history.call_count, 1)
        self.assertEqual(progress.call_count, 1)

    @patch("narrador.interface.actions.getHistory", return_value=[("Teste", "teste")])
    def test_segmento_salvo_atualiza_tabela_sem_resetar_selecao_ou_player(self, history):
        saved = deepcopy(self.data)
        saved["segmentos"][0].update(arquivo="trecho.wav", duracao_s=3.47)
        saved["mensagem"] = "Segmento 1 salvo."
        updates = getNarrationState(saved, previousData=self.data)
        self.assertEqual(updates[1], "Segmento 1 salvo.")
        self.assertEqual(updates[5][0], [1, "Que história incrível!", "Salvo", 3.5])
        for index in (0, 2, 3, 4, 6):
            self.assertEqual(updates[index], gr.skip())
        history.assert_not_called()

    @patch("narrador.interface.actions.getHistory", return_value=[("Teste", "teste")])
    def test_conclusao_exibe_apenas_mp3_e_atualiza_historico(self, history):
        completed = deepcopy(self.data)
        completed.update(status="concluido", mensagem="Narração concluída.")
        completed["resultado"] = {"mp3": "narracao.mp3", "duracao_s": 8}
        updates = getNarrationState(completed, previousData=self.data)
        self.assertEqual(len(updates), 7)
        self.assertTrue(updates[2].endswith("narracao.mp3"))
        self.assertEqual(updates[2], updates[3])
        self.assertNotIn("WAV", updates[1])
        self.assertEqual(updates[4], gr.skip())
        history.assert_called_once()

    @patch("narrador.interface.actions.getHistory", return_value=[("Teste", "teste")])
    def test_snapshot_anterior_nao_e_alterado_pelo_controlador(self, history):
        def snapshots():
            yield self.data
            self.data["segmentos"][0].update(arquivo="trecho.wav", duracao_s=3)
            yield self.data

        updates = list(streamNarrationState(snapshots(), Mock()))
        self.assertEqual(len(updates), 2)
        self.assertEqual(updates[1][5][0][2], "Salvo")
        self.assertEqual(updates[1][4], gr.skip())

    def test_cancelamento_mostra_velocidade_da_exportacao_preservada(self):
        self.data["resultado"] = {"mp3": "anterior.mp3", "duracao_s": 8, "velocidade": 1}
        self.data["parametros"]["velocidade"] = 1.1
        for status in ("erro", "cancelado"):
            self.data["status"] = status
            message = getStatusMessage(self.data)
            self.assertIn("velocidade 1.00×", message)
            self.assertNotIn("1.10×", message)
            self.assertIn("última exportação completa", message)

    @patch("narrador.interface.view.getVoiceReferences", return_value={})
    @patch("narrador.interface.view.getHistory", return_value=[])
    def test_configuracao_mp3_e_progresso_nao_cobrem_segmentos(self, history, references):
        demo = buildInterface()
        config = demo.config
        labels = [component["props"].get("label") for component in config["components"]]
        self.assertIn("Baixar MP3", labels)
        self.assertNotIn("Baixar WAV", labels)
        statusId = next(component["id"] for component in config["components"]
                        if component["props"].get("elem_id") == "progresso")
        segmentId = next(component["id"] for component in config["components"]
                         if component["props"].get("elem_id") == "lista-segmentos")
        generationEvents = [event for event in config["dependencies"]
                            if event["api_name"] in ("gerar", "gerar_1", "regenerar")]
        self.assertEqual(len(generationEvents), 3)
        for event in generationEvents:
            self.assertEqual(len(event["outputs"]), 7)
            self.assertEqual(event["show_progress"], "minimal")
            self.assertEqual(event["show_progress_on"], [statusId])
        selection = next(event for event in config["dependencies"]
                         if event["api_name"] == "ouvir_segmento")
        self.assertEqual(selection["targets"], [(segmentId, "input")])
        loadFunction = next(function for function in demo.fns.values()
                            if function.api_name == "carregar")
        self.assertEqual(loadFunction.concurrency_id, "gpu")
        self.assertEqual(loadFunction.concurrency_limit, 1)
        expressive = next(component for component in config["components"]
                          if component["props"].get("label") == "Expressividade")
        self.assertEqual(expressive["props"]["value"], ESTILOS["Narrador natural"].expressividade)


if __name__ == "__main__":
    unittest.main()
