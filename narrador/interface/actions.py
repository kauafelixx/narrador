"""Callbacks da interface. Encaminham a síntese ao controlador já existente."""

import logging
import subprocess
from copy import deepcopy

import gradio as gr
import psutil

from narrador.controller import CONTROLADOR as audioController
from narrador.controller import validar_parametros as validateParameters
from narrador.paths import OUTPUTS
from narrador.storage import historico as getHistory
from narrador.storage import ler_job as readJob
from narrador.texto import segmentar as splitScript


def showResult():
    return gr.Tabs(selected="resultado")


def prepareGeneration():
    return showResult(), None


def getSegmentChoices(data):
    return [
        (f"{segment['numero']:02d} · {segment['texto'][:85]}", segmentIndex)
        for segmentIndex, segment in enumerate(data["segmentos"])
    ]


def getSegmentRows(data):
    return [
        [
            segment["numero"], segment["texto"],
            "Salvo" if segment.get("arquivo") else "Pendente",
            round(segment.get("duracao_s", 0), 1),
        ]
        for segment in data["segmentos"]
    ]


def getStatusMessage(data):
    result = data.get("resultado") or {}
    message = data.get("mensagem", data["status"])
    if result.get("duracao_s"):
        speed = result.get("velocidade", data["parametros"]["velocidade"])
        message += f"\n\nDuração: {result['duracao_s'] / 60:.2f} min · MP3 · velocidade {speed:.2f}×."
    if result.get("aviso"):
        message += f"\n\n{result['aviso']}"
    if data.get("status") in ("cancelado", "erro", "parcial") and result.get("mp3"):
        message += "\n\nO reprodutor mantém a última exportação completa deste projeto."
    return message


def getNarrationState(data, selectedSegment=None, previousData=None):
    """Atualiza somente os controles cujo conteúdo realmente mudou.

    O controlador consulta o projeto a cada meio segundo. Recriar dropdowns e
    tabelas em todas essas consultas reinicia seleção, player e renderização.
    A comparação é local a cada geração, sem compartilhar estado entre sessões.
    """
    outputDirectory = OUTPUTS / data["id"]
    result = data.get("resultado") or {}
    mp3 = str(outputDirectory / result["mp3"]) if result.get("mp3") else None
    segmentRows = getSegmentRows(data)
    message = getStatusMessage(data)
    choices = getSegmentChoices(data)
    value = selectedSegment if selectedSegment is not None else 0 if choices else None
    firstUpdate = previousData is None or previousData["id"] != data["id"]
    updates = [gr.skip() for _ in range(7)]
    if firstUpdate:
        updates[0] = data["id"]
    if firstUpdate or message != getStatusMessage(previousData):
        updates[1] = message
    if firstUpdate or result.get("mp3") != (previousData.get("resultado") or {}).get("mp3"):
        updates[2] = mp3
        updates[3] = mp3
    if firstUpdate or choices != getSegmentChoices(previousData):
        updates[4] = gr.Dropdown(choices=choices, value=value)
    if firstUpdate or segmentRows != getSegmentRows(previousData):
        updates[5] = segmentRows
    if firstUpdate or (
        data.get("status") != previousData.get("status")
        and data.get("status") in ("concluido", "cancelado", "erro", "parcial")
    ):
        updates[6] = gr.Dropdown(choices=getHistory(), value=data["id"])
    return tuple(updates)


def streamNarrationState(dataStream, progress, selectedSegment=None):
    previousData = None
    for data in dataStream:
        state = getNarrationState(data, selectedSegment, previousData)
        previousData = deepcopy(data)
        if all(value == gr.skip() for value in state):
            continue
        progress(
            (data.get("concluidos", 0), max(1, data.get("total_tarefa", 1))),
            desc=data.get("mensagem", "Gerando…"),
        )
        yield state


def generateNarration(
    scriptText,
    voiceChoice,
    referenceUpload,
    voiceConsent,
    styleChoice,
    expressiveness,
    temperature,
    cfg,
    speed,
    seed,
    progress=gr.Progress(),
):
    try:
        parameters = validateParameters(
            styleChoice, expressiveness, temperature, cfg, speed, seed
        )
        yield from streamNarrationState(
            audioController.gerar(
                scriptText, voiceChoice, referenceUpload, voiceConsent, parameters
            ), progress,
        )
    except Exception as exc:
        logging.exception("Falha na geração")
        raise gr.Error(str(exc)) from exc


def regenerateSegment(
    jobId,
    segmentIndex,
    styleChoice,
    expressiveness,
    temperature,
    cfg,
    speed,
    seed,
    progress=gr.Progress(),
):
    try:
        parameters = validateParameters(
            styleChoice, expressiveness, temperature, cfg, speed, seed
        )
        yield from streamNarrationState(
            audioController.gerar(
                None, None, None, True, parameters, jobId, segmentIndex
            ), progress, segmentIndex,
        )
    except Exception as exc:
        logging.exception("Falha na regeneração")
        raise gr.Error(str(exc)) from exc


def loadGeneration(jobId):
    try:
        data = readJob(jobId)
        parameters = data["parametros"]
        return (
            *getNarrationState(data),
            data["texto"],
            parameters["estilo"],
            parameters["expressividade"],
            parameters["temperatura"],
            parameters["cfg"],
            parameters["velocidade"],
            parameters["semente"],
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def getSegmentAudio(jobId, segmentIndex):
    if not jobId or segmentIndex is None:
        return None
    data = readJob(jobId)
    segment = data["segmentos"][int(segmentIndex)]
    return str(OUTPUTS / jobId / segment["arquivo"]) if segment.get("arquivo") else None


def analyzeScript(scriptText, styleChoice):
    try:
        segments = splitScript(scriptText, styleChoice)
        wordCount = len(scriptText.split())
        return f"{wordCount} palavras · {len(segments)} segmentos · aproximadamente {wordCount / 150:.1f} min de fala a 1×. A duração real varia com a interpretação."
    except ValueError as exc:
        return str(exc)


def getResources():
    memoryInfo = psutil.virtual_memory()
    message = f"RAM do sistema: {memoryInfo.used / 1024**3:.1f} / {memoryInfo.total / 1024**3:.1f} GB"
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode == 0:
            usedMemory, totalMemory, gpuUsage, gpuTemperature = (
                result.stdout.strip().splitlines()[0].split(", ")
            )
            message += f" · VRAM: {usedMemory} / {totalMemory} MB · GPU: {gpuUsage}% · {gpuTemperature} °C"
    except (OSError, subprocess.SubprocessError, ValueError):
        message += " · Monitor da GPU indisponível"
    return message
