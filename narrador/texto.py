"""Texto original preservado; datas recebem uma forma explícita para a fala."""
import re
import unicodedata
from dataclasses import dataclass
from datetime import date


_UNIDADES = ("zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove",
             "dez", "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete",
             "dezoito", "dezenove")
_DEZENAS = ("", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa")
_CENTENAS = ("", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos",
             "seiscentos", "setecentos", "oitocentos", "novecentos")
_MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
          "setembro", "outubro", "novembro", "dezembro")
_LIMITE_NUMERO = r"(?![\w/:-]|\.\d|,\d)"
_CONTEXTO_ANO = r"(?:anos?(?:\s+de)?|em|desde|até|entre|durante|antes\s+de|depois\s+de|por\s+volta\s+de|a\s+partir\s+de)"
_DATAS = (
    re.compile(r"(?<![\w/.-])(?P<dia>\d{1,2})(?P<sep>[/\-])(?P<mes>\d{1,2})(?P=sep)(?P<ano>\d{4})(?![\w/-]|\.\d)"),
    re.compile(r"(?<![\w/.-])(?P<ano>\d{4})-(?P<mes>\d{2})-(?P<dia>\d{2})(?![\w/-]|\.\d)"),
    re.compile(r"\b(?P<rotulo>(?:data|dia)\s*(?::\s*|\s+))(?P<dia>\d{1,2})\.(?P<mes>\d{1,2})\.(?P<ano>\d{4})(?![\w/-]|\.\d)", re.I),
)
_DATA_ESCRITA = re.compile(
    r"\b(?P<dia>\d{1,2})[º°]?\s+de\s+(?P<mes>" + "|".join(_MESES) +
    r")(?:\s+de\s+(?P<ano>\d{4})" + _LIMITE_NUMERO + r")?\b", re.I)
_ANOS_INTERVALO = re.compile(
    r"\b(?P<contexto>entre|(?:nos?\s+)?anos?(?:\s+de)?|de)\s+(?P<ano>[1-9]\d{3})\s+"
    r"(?P<ligacao>e|a|até|–|—|-)\s+(?P<fim>[1-9]\d{3})" + _LIMITE_NUMERO, re.I)
_ANO = re.compile(r"\b(?P<contexto>" + _CONTEXTO_ANO + r")\s+(?P<ano>[1-9]\d{3})" + _LIMITE_NUMERO, re.I)
_IDENTIFICADOR = re.compile(
    r"\b(?:c[oó]digo|vers[aã]o|telefone|tel\.?|celular|whatsapp|cpf|cnpj|cep|protocolo|matr[ií]cula|id)"
    r"\s*(?:de\s+|n[ºo.]?\s*|:\s*)?$", re.I)


def _cardinal(numero):
    """Cardinais usados em dias e anos, sem dependências de idioma externas."""
    if not 0 <= numero <= 9999:
        raise ValueError("Número fora do intervalo de datas suportado.")
    if numero < 20:
        return _UNIDADES[numero]
    if numero < 100:
        dezena, resto = divmod(numero, 10)
        return _DEZENAS[dezena] + (" e " + _cardinal(resto) if resto else "")
    if numero == 100:
        return "cem"
    if numero < 1000:
        centena, resto = divmod(numero, 100)
        return _CENTENAS[centena] + (" e " + _cardinal(resto) if resto else "")
    milhar, resto = divmod(numero, 1000)
    inicio = ("" if milhar == 1 else _cardinal(milhar) + " ") + "mil"
    if not resto:
        return inicio
    return inicio + (" e " if resto < 100 or resto % 100 == 0 else " ") + _cardinal(resto)


def _eh_identificador(texto, inicio):
    return bool(_IDENTIFICADOR.search(texto[max(0, inicio-45):inicio]))


def _data_por_extenso(match):
    dia, mes, ano = (int(match[chave]) for chave in ("dia", "mes", "ano"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return match[0]
    rotulo = match.groupdict().get("rotulo") or ""
    return rotulo + ("primeiro" if dia == 1 else _cardinal(dia)) + " de " + _MESES[mes-1] + " de " + _cardinal(ano)


def normalizar_fala(texto):
    """Expande datas válidas e anos com contexto, mantendo acentos e pontuação.

    Números isolados e identificadores ficam intactos. O roteiro exibido/salvo
    continua original; esta forma é usada apenas como entrada da síntese.
    """
    texto = unicodedata.normalize("NFC", texto)
    for padrao in _DATAS:
        original = texto
        texto = padrao.sub(lambda m: m[0] if _eh_identificador(original, m.start()) else _data_por_extenso(m), texto)

    def data_escrita(match):
        dia = int(match["dia"])
        mes = _MESES.index(match["mes"].lower()) + 1
        ano = int(match["ano"]) if match["ano"] else None
        try:
            date(2000 if ano is None else ano, mes, dia)
        except ValueError:
            return match[0]
        return (("primeiro" if dia == 1 else _cardinal(dia)) + " de " + match["mes"] +
                (" de " + _cardinal(ano) if ano else ""))

    texto = _DATA_ESCRITA.sub(data_escrita, texto)
    original = texto
    texto = _ANOS_INTERVALO.sub(
        lambda m: m[0] if _eh_identificador(original, m.start()) else
        f"{m['contexto']} {_cardinal(int(m['ano']))} {m['ligacao']} {_cardinal(int(m['fim']))}", texto)
    original = texto
    return _ANO.sub(lambda m: m[0] if _eh_identificador(original, m.start()) else
                    f"{m['contexto']} {_cardinal(int(m['ano']))}", texto)


@dataclass(frozen=True)
class Estilo:
    expressividade: float
    temperatura: float
    cfg: float
    caracteres: int
    pausa_frase: float
    pausa_paragrafo: float


ESTILOS = {
    "Narrador natural": Estilo(.60, .75, .35, 280, .22, .55),
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
    frases = []
    inicio = 0
    # Fecha a frase depois das aspas/parênteses, conservando ?! e reticências.
    for final in re.finditer(r'''[.!?…]+["'”’»)\]}]*(?=\s+|$)''', protegido):
        frases.append(protegido[inicio:final.end()].replace("\ue000", ".").strip())
        inicio = final.end()
    restante = protegido[inicio:].replace("\ue000", ".").strip()
    if restante:
        frases.append(restante)
    return [frase for frase in frases if frase]


def _limitar(frase, limite):
    while len(frase) > limite or len(normalizar_fala(frase)) > limite:
        # Mantém data e contexto do ano juntos, mesmo quando a expansão ocupa
        # mais caracteres que os algarismos no roteiro original.
        protegidos = []
        for padrao in (*_DATAS, _DATA_ESCRITA, _ANOS_INTERVALO, _ANO):
            for match in padrao.finditer(frase):
                inicio = match.start()
                deslocamento = max(0, inicio-45)
                identificador = _IDENTIFICADOR.search(frase[deslocamento:inicio])
                if identificador:
                    inicio = deslocamento + identificador.start()
                protegidos.append((inicio, match.end()))
        candidatos = []
        for espaco in re.finditer(r"\s+", frase[:limite+1]):
            corte = espaco.end()
            if any(inicio < corte < fim for inicio, fim in protegidos):
                continue
            parte = frase[:corte].strip()
            if len(parte) <= limite and len(normalizar_fala(parte)) <= limite:
                candidatos.append(corte)
        preferidos = [corte for corte in candidatos
                      if len(normalizar_fala(frase[:corte].strip())) >= limite // 3
                      and frase[:corte].rstrip().endswith((",", ";", ":"))]
        if not candidatos:
            raise ValueError("Há uma palavra muito longa. Insira espaços no roteiro.")
        corte = preferidos[-1] if preferidos else candidatos[-1]
        yield frase[:corte].strip(), "clausula"
        frase = frase[corte:].strip()
    if frase:
        yield frase, "frase"


def _pausa(parte, tipo, config):
    if tipo == "clausula":
        return .12 if parte.endswith((",", ";", ":")) else .04
    final = parte.rstrip().rstrip('"\'”’»)]}').rstrip()
    if final.endswith(("…", "...")):
        return round(config.pausa_frase + .18, 2)
    if final.endswith(("?", "!")):
        return round(config.pausa_frase + (.10 if "?" in final[-3:] else .06), 2)
    return config.pausa_frase


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
                                  "texto_fala": normalizar_fala(parte),
                                  "pausa": _pausa(parte, tipo, config),
                                  "arquivo": None})
        segmentos[-1]["pausa"] = config.pausa_paragrafo
    segmentos[-1]["pausa"] = 0
    return segmentos

