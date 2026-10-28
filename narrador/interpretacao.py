"""Variações moderadas de interpretação com os controles reais do Multilingual."""

import re


def texto_para_modelo(texto):
    """Mantém !? no fim, evitando o ponto que o motor acrescenta após aspas."""
    return re.sub(r'''([!?]+)(["'”’»)\]}]+)\s*$''', r"\2\1", texto)


def parametros_trecho(texto, parametros):
    """A pontuação continua no texto; a emoção não depende de tags artificiais."""
    final = texto.rstrip().rstrip('\"\'”’»)]}').rstrip()
    expressividade = parametros["expressividade"]
    if re.search(r"[!?]+$", final):
        expressividade += .08 if "!" in re.search(r"[!?]+$", final)[0] else .03
    return {"exaggeration": round(min(1.5, expressividade), 3),
            "temperature": parametros["temperatura"], "cfg_weight": parametros["cfg"],
            "repetition_penalty": 1.2, "min_p": .05, "top_p": 1.0}
