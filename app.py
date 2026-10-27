"""Ponto de entrada. Prepara o modo offline antes de importar a interface."""

import os

from narrador.paths import ROOT, configure


def main():
    configure(offline=True)
    os.environ["GRADIO_TEMP_DIR"] = str(ROOT / ".cache" / "gradio")

    from narrador.launcher import runApp

    runApp()


if __name__ == "__main__":
    main()
