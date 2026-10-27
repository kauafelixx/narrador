"""Interface visual do Narrador, separada do motor de geração."""

from .theme import buildTheme, getLocaleScript, loadStyleSheet
from .view import buildInterface

__all__ = ["buildInterface", "buildTheme", "getLocaleScript", "loadStyleSheet"]
