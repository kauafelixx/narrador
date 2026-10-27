"""Callbacks da interface. Encaminham a síntese ao controlador já existente."""

import logging
import subprocess

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


def getSegmentChoices(data):
    return [
        (f"{segment['numero']:02d} · {segment['texto'][:85]}", segmentIndex)
        for segmentIndex, segment in enumerate(data["segmentos"])
    ]


def getNarrationState(data, selectedSegment=None):
    outputDirectory = OUTPUTS / data["id"]
    result = data.get("resultado") or {}
    wav = str(outputDirectory / result["wav"]) if result.get("wav") else None
    mp3 = str(outputDirectory / result["mp3"]) if result.get("mp3") else None
    segmentRows = [
        [
            segment["numero"],
            segment["texto"],
            "Salvo" if segment.get("arquivo") else "Pendente",
            round(segment.get("duracao_s", 0), 1),
        ]
        for segment in data["segmentos"]
    ]
    message = data.get("mensagem", data["status"])
    if result.get("duracao_s"):
        message += f"\n\nDuração: {result['duracao_s'] / 60:.2f} min · WAV em 24 kHz · velocidade {data['parametros']['velocidade']:.2f}×."
    if result.get("aviso"):
        message += f"\n\n{result['aviso']}"
    if data.get("status") in ("cancelado", "erro", "parcial") and result.get("wav"):
        message += "\n\nO reprodutor mantém a última exportação completa deste projeto."
    choices = getSegmentChoices(data)
    value = selectedSegment if selectedSegment is not None else 0 if choices else None
    return (
        data["id"],
        message,
        wav,
        wav,
        mp3,
        gr.Dropdown(choices=choices, value=value),
        segmentRows,
        gr.Dropdown(choices=getHistory(), value=data["id"]),
    )


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
        for data in audioController.gerar(
            scriptText, voiceChoice, referenceUpload, voiceConsent, parameters
        ):
            progress(
                (data.get("concluidos", 0), max(1, data.get("total_tarefa", 1))),
                desc=data.get("mensagem", "Gerando…"),
            )
            yield getNarrationState(data)
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
        for data in audioController.gerar(
            None, None, None, True, parameters, jobId, segmentIndex
        ):
            progress(
                (data.get("concluidos", 0), 1),
                desc=data.get("mensagem", "Regenerando…"),
            )
            yield getNarrationState(data, segmentIndex)
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
