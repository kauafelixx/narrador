"""Segmentação conservadora: pontuação e ordem preservadas."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Estilo:
    expressividade: float
    temperatura: float
    cfg: float
    caracteres: int
    pausa_frase: float
    pausa_paragrafo: float


ESTILOS = {
    "Narrador natural": Estilo(.50, .80, .50, 280, .22, .55),
    "Narrador solene": Estilo(.45, .70, .35, 240, .36, .80),
    "Narrador emocionante": Estilo(.70, .85, .35, 240, .28, .65),
    "Narrador dramático": Estilo(.80, .85, .30, 220, .40, .85),
    "Narrador com suspense": Estilo(.60, .70, .30, 220, .48, .95),
    "Narrador energético": Estilo(.75, .90, .45, 260, .16, .40),
}


def _frases(paragrafo):
    # Protege abreviações comuns, iniciais e números decimais.
    protegido = re.sub(r"\b(?:Sr|Sra|Srta|Dr|Dra|D|Pe|Prof|Profa|etc|pág|cap)\.",
                       lambda m: m[0].replace(".", "\ue000"), paragrafo, flags=re.I)
    protegido = re.sub(r"\b[A-ZÁÉÍÓÚ]\.(?=\s+[A-ZÁÉÍÓÚ])",
                       lambda m: m[0].replace(".", "\ue000"), protegido)
    protegido = re.sub(r"(?<=\d)\.(?=\d)", "\ue000", protegido)
    return [s.replace("\ue000", ".").strip() for s in
            re.split(r'(?<=[.!?…])\s+(?=[\w“"‘\(—-])', protegido) if s.strip()]


def _limitar(frase, limite):
    while len(frase) > limite:
        candidatos = [m.end() for m in re.finditer(r"[,;:]\s+", frase[:limite+1])
                      if m.end() >= limite // 3]
        corte = candidatos[-1] if candidatos else frase.rfind(" ", 0, limite+1)
        if corte <= 0:
            raise ValueError("Há uma palavra muito longa. Insira espaços no roteiro.")
        yield frase[:corte].strip(), "clausula"
        frase = frase[corte:].strip()
    if frase:
        yield frase, "frase"


def segmentar(texto, estilo="Narrador natural"):
    texto = texto.strip().replace("\r\n", "\n").replace("\r", "\n")
    if not texto:
        raise ValueError("Digite o roteiro antes de gerar a narração.")
    if len(texto) > 30000 or len(texto.split()) > 2000:
        raise ValueError("Use até 2.000 palavras e 30.000 caracteres por projeto. Divida roteiros maiores.")
    if "\ue000" in texto:
        raise ValueError("Remova o caractere privado U+E000 do texto.")
    config = ESTILOS[estilo]
    segmentos = []
    for paragrafo in re.split(r"\n\s*\n", texto):
        paragrafo = re.sub(r"\s+", " ", paragrafo).strip()
        if not paragrafo:
            continue
        for frase in _frases(paragrafo):
            for parte, tipo in _limitar(frase, config.caracteres):
                segmentos.append({"numero": len(segmentos)+1, "texto": parte,
                                  "pausa": .12 if tipo == "clausula" else config.pausa_frase,
                                  "arquivo": None})
        segmentos[-1]["pausa"] = config.pausa_paragrafo
    segmentos[-1]["pausa"] = 0
    return segmentos

