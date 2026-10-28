"""Referências tipadas aos controles usados pelos eventos da interface."""

from dataclasses import dataclass
from pathlib import Path

import gradio as gr


@dataclass(frozen=True)
class InterfaceElements:
    outputTabs: gr.Tabs
    job: gr.State
    timer: gr.Timer
    segmentTable: gr.Dataframe
    resourceMonitor: gr.Textbox
    scriptText: gr.Textbox
    scriptEstimate: gr.Markdown
    voiceChoice: gr.Dropdown
    repeatButton: gr.Button
    styleChoice: gr.Dropdown
    speed: gr.Slider
    referencePreview: gr.Audio
    referenceUpload: gr.Audio
    voiceConsent: gr.Checkbox
    expressiveness: gr.Slider
    temperature: gr.Slider
    cfg: gr.Slider
    seed: gr.Number
    generateButton: gr.Button
    cancelButton: gr.Button
    status: gr.Textbox
    fullAudio: gr.Audio
    generationHistory: gr.Dropdown
    segmentChoice: gr.Dropdown
    segmentAudio: gr.Audio
    regenerateButton: gr.Button
    mp3: gr.File
    loadButton: gr.Button
    refreshButton: gr.Button
    voiceReferences: dict[str, Path]
