"""Tema, fonte local, estilos e idioma dos controles Gradio."""

import re
from pathlib import Path

import gradio as gr

from narrador.paths import ROOT

styleFiles = ("base.css", "layout.css", "controls.css", "responsive.css")


def loadStyleSheet():
    styleDirectory = ROOT / "assets" / "styles"
    return "\n\n".join(
        (styleDirectory / fileName).read_text(encoding="utf-8")
        for fileName in styleFiles
    )


def buildTheme():
    theme = gr.themes.Soft(
        primary_hue="orange",
        secondary_hue="orange",
        neutral_hue="slate",
        font=["Montserrat", "Arial", "sans-serif"],
        font_mono=["Montserrat", "Arial", "sans-serif"],
    ).set(
        body_background_fill="#F7F8FA",
        body_background_fill_dark="#F7F8FA",
        body_text_color="#263241",
        body_text_color_dark="#263241",
        body_text_color_subdued="#667180",
        body_text_color_subdued_dark="#667180",
        block_background_fill="#FFFFFF",
        block_background_fill_dark="#FFFFFF",
        block_border_color="#E5E9EE",
        block_border_color_dark="#E5E9EE",
        block_label_background_fill="transparent",
        block_label_background_fill_dark="transparent",
        block_label_text_color="#263241",
        block_label_text_color_dark="#263241",
        block_title_text_color="#263241",
        block_title_text_color_dark="#263241",
        block_shadow="none",
        block_shadow_dark="none",
        input_background_fill="#FFFFFF",
        input_background_fill_dark="#FFFFFF",
        input_background_fill_focus="#FFFFFF",
        input_background_fill_focus_dark="#FFFFFF",
        input_border_color="#DFE5EB",
        input_border_color_dark="#DFE5EB",
        input_border_color_focus="#C94A0A",
        input_border_color_focus_dark="#C94A0A",
        input_placeholder_color="#747E8A",
        input_placeholder_color_dark="#747E8A",
        button_primary_background_fill="#C94A0A",
        button_primary_background_fill_dark="#C94A0A",
        button_primary_background_fill_hover="#AA3C05",
        button_primary_background_fill_hover_dark="#AA3C05",
        button_primary_text_color="#FFFFFF",
        button_primary_text_color_dark="#FFFFFF",
        button_primary_border_color="#C94A0A",
        button_primary_border_color_dark="#C94A0A",
        button_secondary_background_fill="#FFFFFF",
        button_secondary_background_fill_dark="#FFFFFF",
        button_secondary_text_color="#53606F",
        button_secondary_text_color_dark="#53606F",
        button_secondary_border_color="#DFE5EB",
        button_secondary_border_color_dark="#DFE5EB",
    )
    # O pedido é uma interface branca mesmo quando o navegador usa tema escuro.
    themeValues = theme.to_dict()["theme"]
    darkOverrides = {
        key: themeValues[key.removesuffix("_dark")]
        for key in themeValues
        if key.endswith("_dark") and key.removesuffix("_dark") in themeValues
    }
    return theme.set(**darkOverrides)


def getLocaleScript():
    assets = Path(gr.__file__).parent / "templates" / "frontend" / "assets"
    bundle = next(assets.glob("i18n-*.js"))
    source = bundle.read_text(encoding="utf-8")
    if not re.search("\\bas \\$[,}]", source):
        raise RuntimeError("A versão do Gradio mudou. Revise a integração de idioma.")
    return (
        "async () => { const { $: idioma } = await import('/assets/"
        + bundle.name
        + "'); await idioma.set('pt-BR'); }"
    )
