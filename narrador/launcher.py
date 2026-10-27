"""Inicialização local e ciclo de vida da interface, sem lógica de síntese."""

import argparse
import json
import logging
import webbrowser
from urllib.error import URLError
from urllib.request import urlopen

from narrador.controller import CONTROLADOR as audioController
from narrador.instance import AppAlreadyRunningError, instanceLock
from narrador.paths import LOGS, OUTPUTS, ROOT

from .interface import buildInterface, buildTheme, getLocaleScript, loadStyleSheet


def openExistingInstance(port: int, openBrowser: bool):
    """Reabre somente o servidor local que se identifica como o Narrador."""
    localUrl = f"http://127.0.0.1:{port}"
    try:
        with urlopen(f"{localUrl}/config", timeout=3) as response:
            serverConfig = json.load(response)
        isNarrador = serverConfig.get("title") == "Narrador · Seu estúdio de voz"
    except (URLError, OSError, ValueError):
        isNarrador = False
    if isNarrador:
        print(f"O Narrador já está aberto em {localUrl}.")
        if openBrowser:
            webbrowser.open(localUrl)
    else:
        print(
            "O Narrador já está em execução ou ainda está inicializando. "
            "Aguarde e use a janela existente."
        )


def runApp():
    argumentParser = argparse.ArgumentParser(description="Narrador local")
    argumentParser.add_argument("--sem-navegador", action="store_true")
    argumentParser.add_argument("--porta", type=int, default=7860)
    arguments = argumentParser.parse_args()
    logging.basicConfig(
        filename=LOGS / "interface.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )
    try:
        with instanceLock():
            launchStudio(arguments)
    except AppAlreadyRunningError:
        openExistingInstance(arguments.porta, not arguments.sem_navegador)
    except PermissionError as error:
        logging.exception("Falha de acesso durante a inicialização")
        raise SystemExit(
            "Não foi possível acessar um arquivo do projeto. "
            "Confira o acesso à pasta. Detalhes em logs/interface.log."
        ) from error


def launchStudio(arguments):
    """Executa a interface enquanto a instância mantém seu bloqueio."""
    studio = buildInterface()
    try:
        studio.queue(max_size=1, default_concurrency_limit=1, api_open=False).launch(
            server_name="127.0.0.1",
            server_port=arguments.porta,
            share=False,
            inbrowser=not arguments.sem_navegador,
            show_error=True,
            mcp_server=False,
            footer_links=[],
            js=getLocaleScript(),
            css=loadStyleSheet(),
            theme=buildTheme(),
            allowed_paths=[
                str(OUTPUTS),
                str(ROOT / "references"),
                str(ROOT / "assets"),
            ],
            blocked_paths=[
                str(ROOT / ".venv"),
                str(ROOT / "models"),
                str(ROOT / ".cache" / "huggingface"),
            ],
            max_file_size="50mb",
        )
    finally:
        audioController.cancelar()
        studio.close()
