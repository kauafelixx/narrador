"""Liga os controles aos callbacks sem alterar a fila de geração."""

import gradio as gr

from narrador.controller import CONTROLADOR as audioController
from narrador.storage import historico as getHistory
from narrador.texto import ESTILOS as narrationStyles

from .actions import (
    analyzeScript,
    generateNarration,
    getResources,
    getSegmentAudio,
    loadGeneration,
    prepareGeneration,
    regenerateSegment,
    showResult,
)
from .elements import InterfaceElements


def connectEvents(elements: InterfaceElements, studio: gr.Blocks):
    elements.timer.tick(
        getResources,
        outputs=elements.resourceMonitor,
        queue=False,
        show_progress="hidden",
        api_visibility="private",
        api_name="recursos",
    )
    studio.load(
        getResources,
        outputs=elements.resourceMonitor,
        queue=False,
        api_visibility="private",
        api_name="recursos",
    )
    generationInputs = [
        elements.scriptText,
        elements.voiceChoice,
        elements.referenceUpload,
        elements.voiceConsent,
        elements.styleChoice,
        elements.expressiveness,
        elements.temperature,
        elements.cfg,
        elements.speed,
        elements.seed,
    ]
    voiceSettings = [
        elements.styleChoice,
        elements.expressiveness,
        elements.temperature,
        elements.cfg,
        elements.speed,
        elements.seed,
    ]
    generationOutputs = [
        elements.job,
        elements.status,
        elements.fullAudio,
        elements.mp3,
        elements.segmentChoice,
        elements.segmentTable,
        elements.generationHistory,
    ]
    for button in (elements.generateButton, elements.repeatButton):
        resultEvent = button.click(
            prepareGeneration,
            outputs=[elements.outputTabs, elements.segmentAudio],
            queue=False,
            api_visibility="private",
        )
        generationEvent = resultEvent.then(
            generateNarration,
            generationInputs,
            generationOutputs,
            concurrency_id="gpu",
            concurrency_limit=1,
            trigger_mode="once",
            show_progress="minimal",
            show_progress_on=elements.status,
            api_visibility="private",
            api_name="gerar",
        )
        generationEvent.success(
            getSegmentAudio,
            [elements.job, elements.segmentChoice],
            elements.segmentAudio,
            show_progress="hidden",
            api_visibility="private",
        )
    regenerateEvent = elements.regenerateButton.click(
        regenerateSegment,
        [elements.job, elements.segmentChoice, *voiceSettings],
        generationOutputs,
        concurrency_id="gpu",
        concurrency_limit=1,
        trigger_mode="once",
        show_progress="minimal",
        show_progress_on=elements.status,
        api_visibility="private",
        api_name="regenerar",
    )
    regenerateEvent.success(
        getSegmentAudio,
        [elements.job, elements.segmentChoice],
        elements.segmentAudio,
        show_progress="hidden",
        api_visibility="private",
    )
    elements.cancelButton.click(
        audioController.cancelar,
        outputs=elements.status,
        queue=False,
        api_visibility="private",
    )
    loadEvent = elements.loadButton.click(
        loadGeneration,
        elements.generationHistory,
        [*generationOutputs, elements.scriptText, *voiceSettings],
        concurrency_id="gpu",
        concurrency_limit=1,
        api_visibility="private",
        api_name="carregar",
    )
    loadEvent.success(
        showResult,
        outputs=elements.outputTabs,
        queue=False,
        api_visibility="private",
    )
    loadEvent.success(
        getSegmentAudio,
        [elements.job, elements.segmentChoice],
        elements.segmentAudio,
        show_progress="hidden",
        api_visibility="private",
    )
    elements.refreshButton.click(
        lambda: gr.Dropdown(choices=getHistory()),
        outputs=elements.generationHistory,
        queue=False,
        api_visibility="private",
    )
    elements.segmentChoice.input(
        getSegmentAudio,
        [elements.job, elements.segmentChoice],
        elements.segmentAudio,
        show_progress="hidden",
        api_visibility="private",
        api_name="ouvir_segmento",
    )
    elements.voiceChoice.change(
        lambda voiceName: (
            str(elements.voiceReferences[voiceName])
            if voiceName in elements.voiceReferences
            else None
        ),
        elements.voiceChoice,
        elements.referencePreview,
        queue=False,
        api_visibility="private",
    )
    elements.styleChoice.change(
        lambda voiceName: (
            narrationStyles[voiceName].expressividade,
            narrationStyles[voiceName].temperatura,
            narrationStyles[voiceName].cfg,
        ),
        elements.styleChoice,
        [elements.expressiveness, elements.temperature, elements.cfg],
        queue=False,
        api_visibility="private",
    )
    elements.scriptText.change(
        analyzeScript,
        [elements.scriptText, elements.styleChoice],
        elements.scriptEstimate,
        queue=False,
        api_visibility="private",
    )
    elements.styleChoice.change(
        analyzeScript,
        [elements.scriptText, elements.styleChoice],
        elements.scriptEstimate,
        queue=False,
        api_visibility="private",
    )
