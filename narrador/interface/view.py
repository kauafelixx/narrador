"""Composição visual do estúdio: roteiro, saída, histórico e segmentos."""

import gradio as gr

from narrador.controller import referencias as getVoiceReferences
from narrador.paths import ROOT
from narrador.storage import historico as getHistory
from narrador.texto import ESTILOS as narrationStyles

from .actions import analyzeScript
from .elements import InterfaceElements
from .events import connectEvents


def buildInterface():
    voiceReferences = getVoiceReferences()
    voiceChoices = ["Voz padrão do modelo", *voiceReferences]
    default = next(iter(voiceReferences), voiceChoices[0])
    defaultStyle = narrationStyles["Narrador natural"]
    waveform = gr.WaveformOptions(
        waveform_color="#F5C7A5",
        waveform_progress_color="#C94A0A",
        trim_region_color="#F97316",
    )
    with gr.Blocks(
        title="Narrador · Seu estúdio de voz", analytics_enabled=False
    ) as demo:
        gr.HTML(
            (ROOT / "assets" / "cabecalho.html").read_text(encoding="utf-8"),
            elem_id="cabecalho",
        )
        job = gr.State(None)
        with gr.Row(elem_id="mesa-narracao"):
            with gr.Column(scale=7, min_width=0, elem_id="editor"):
                with gr.Column(min_width=0, elem_id="bloco-roteiro"):
                    gr.Markdown(
                        "### Seu roteiro\nEscreva ou cole o texto que você quer narrar.",
                        elem_classes="section-title",
                    )
                    scriptText = gr.Textbox(
                        label="Roteiro",
                        show_label=False,
                        lines=10,
                        placeholder="Sua próxima história começa aqui…\n\nSepare os parágrafos com uma linha em branco para criar pausas.",
                        elem_id="campo-roteiro",
                        value="Em 1830, no coração de Paris, uma jovem religiosa testemunharia um acontecimento que marcaria para sempre a história da Igreja.",
                    )
                    scriptEstimate = gr.Markdown(
                        analyzeScript(
                            "Em 1830, no coração de Paris, uma jovem religiosa testemunharia um acontecimento que marcaria para sempre a história da Igreja.",
                            "Narrador natural",
                        ),
                        elem_id="estimativa",
                    )
                with gr.Column(min_width=0, elem_id="bloco-interpretacao"):
                    with gr.Row(elem_id="interpretacao"):
                        with gr.Column(min_width=220, elem_id="coluna-estilo"):
                            styleChoice = gr.Dropdown(
                                list(narrationStyles),
                                value="Narrador natural",
                                label="Estilo de interpretação",
                                min_width=0,
                                elem_classes=["studio-field", "studio-dropdown"],
                            )
                        with gr.Column(min_width=220, elem_id="coluna-velocidade"):
                            speed = gr.Slider(
                                0.75,
                                1.5,
                                value=1,
                                step=0.05,
                                label="Velocidade",
                                info="1,10 = 1,1×. Preserva o tom da voz.",
                                min_width=0,
                                elem_id="controle-velocidade",
                                elem_classes=["studio-field", "studio-slider"],
                            )
                    voiceChoice = gr.Dropdown(
                        voiceChoices,
                        value=default,
                        label="Voz de referência",
                        elem_classes=["studio-field", "studio-dropdown"],
                    )
                with gr.Accordion(
                    "Ouvir ou enviar uma referência",
                    open=False,
                    elem_id="referencia-voz",
                ):
                    referencePreview = gr.Audio(
                        value=str(voiceReferences[default])
                        if default in voiceReferences
                        else None,
                        label="Ouvir referência selecionada",
                        interactive=False,
                        buttons=[],
                        waveform_options=waveform,
                        elem_id="previa-referencia",
                    )
                    referenceUpload = gr.Audio(
                        sources=["upload"],
                        type="filepath",
                        label="Enviar outra referência",
                        buttons=[],
                        waveform_options=waveform,
                        elem_id="envio-referencia",
                    )
                    gr.Markdown(
                        "O arquivo enviado tem prioridade sobre a voz da lista. Envie pelo menos 3 segundos de fala limpa, sem música. O modelo utiliza até 10 segundos da gravação.",
                        elem_classes="helper-copy",
                    )
                    voiceConsent = gr.Checkbox(
                        value=True,
                        label="Tenho autorização para usar a voz de referência",
                        elem_id="consentimento",
                    )
                with gr.Accordion(
                    "Ajustes avançados da voz", open=False, elem_id="ajustes-voz"
                ):
                    expressiveness = gr.Slider(
                        0.25,
                        1.5,
                        value=defaultStyle.expressividade,
                        step=0.05,
                        label="Expressividade",
                        elem_classes=["studio-field", "studio-slider"],
                    )
                    temperature = gr.Slider(
                        0.1,
                        1.5,
                        value=defaultStyle.temperatura,
                        step=0.05,
                        label="Temperatura (variação da interpretação)",
                        elem_classes=["studio-field", "studio-slider"],
                    )
                    cfg = gr.Slider(
                        0,
                        1,
                        value=defaultStyle.cfg,
                        step=0.05,
                        label="CFG (aderência à voz / ritmo)",
                        elem_classes=["studio-field", "studio-slider"],
                    )
                    seed = gr.Number(
                        value=0,
                        minimum=0,
                        maximum=2**32 - 1,
                        precision=0,
                        label="Semente (0 = nova variação)",
                        elem_classes="studio-field",
                    )
                    gr.Markdown(
                        "Os estilos sugerem expressividade e ritmo; a emoção pode variar. A velocidade preserva o tom da voz.",
                        elem_classes="helper-copy",
                    )
                with gr.Row(elem_id="acoes"):
                    generateButton = gr.Button(
                        "Gerar narração",
                        variant="primary",
                        scale=3,
                        min_width=0,
                        elem_id="gerar",
                    )
                    cancelButton = gr.Button(
                        "Cancelar geração", scale=1, min_width=0, elem_id="cancelar"
                    )
                repeatButton = gr.Button(
                    "Regenerar roteiro inteiro", elem_id="regenerar-tudo"
                )
            with gr.Column(scale=5, min_width=0, elem_id="resultado-painel"):
                gr.Markdown(
                    "### Sua narração\nOuça, baixe ou refine os trechos da sua história.",
                    elem_classes="section-title",
                )
                with gr.Tabs(elem_id="saida-abas") as outputTabs:
                    with gr.Tab("Resultado", id="resultado"):
                        status = gr.Textbox(
                            label="Progresso",
                            show_label=False,
                            value="Tudo pronto para começar. Escolha a voz e clique em Gerar narração.",
                            lines=3,
                            interactive=False,
                            elem_id="progresso",
                        )
                        fullAudio = gr.Audio(
                            label="Narração completa",
                            interactive=False,
                            buttons=[],
                            waveform_options=waveform,
                            elem_id="player-principal",
                        )
                        with gr.Row(elem_id="downloads"):
                            mp3 = gr.File(label="Baixar MP3", min_width=0, height=100)
                        gr.Markdown(
                            "A narração completa fica disponível aqui ao terminar a geração.",
                            elem_classes="helper-copy",
                        )
                    with gr.Tab("Histórico", id="historico"):
                        generationHistory = gr.Dropdown(
                            choices=getHistory(),
                            label="Gerações salvas",
                            value=None,
                            elem_id="geracoes-salvas",
                            elem_classes=["studio-field", "studio-dropdown"],
                        )
                        with gr.Row(elem_id="historico-acoes"):
                            loadButton = gr.Button(
                                "Carregar geração",
                                min_width=0,
                                elem_id="abrir-historico",
                            )
                            refreshButton = gr.Button(
                                "Atualizar lista",
                                min_width=0,
                                elem_id="atualizar-historico",
                            )
                        gr.Markdown(
                            "Escolha uma geração para recuperar o roteiro, os ajustes e os áudios salvos.",
                            elem_classes="helper-copy",
                        )
                    with gr.Tab("Segmentos", id="segmentos"):
                        segmentChoice = gr.Dropdown(
                            choices=[],
                            label="Segmento para ouvir ou regenerar",
                            value=None,
                            elem_id="lista-segmentos",
                            elem_classes=["studio-field", "studio-dropdown"],
                        )
                        segmentAudio = gr.Audio(
                            label="Áudio do segmento selecionado",
                            interactive=False,
                            buttons=[],
                            waveform_options=waveform,
                            elem_id="ouvir-segmento",
                        )
                        regenerateButton = gr.Button(
                            "Regenerar este segmento", elem_id="regenerar-segmento"
                        )
                        gr.Markdown(
                            "Usa a voz salva no projeto e os ajustes atuais. Os outros trechos são preservados e a narração é unida novamente.",
                            elem_classes="helper-copy",
                        )
        with gr.Accordion(
            "Todos os segmentos do roteiro", open=False, elem_id="tabela-painel"
        ):
            segmentTable = gr.Dataframe(
                headers=["Nº", "Texto", "Situação", "Duração (s)"],
                datatype=["number", "str", "str", "number"],
                interactive=False,
                label="Segmentos do roteiro",
                wrap=True,
                elem_id="tabela-segmentos",
            )
        with gr.Accordion("Desempenho do computador", open=False, elem_id="desempenho"):
            resourceMonitor = gr.Textbox(
                label="Uso de memória e GPU",
                value="Verificando recursos…",
                lines=2,
                interactive=False,
                elem_id="monitor-recursos",
            )
        timer = gr.Timer(5)
        gr.Markdown(
            "Seus áudios ficam salvos na pasta `outputs`. Para encerrar o aplicativo, pressione Ctrl+C na janela do programa.",
            elem_id="rodape",
        )
        elements = InterfaceElements(
            outputTabs=outputTabs,
            job=job,
            timer=timer,
            segmentTable=segmentTable,
            resourceMonitor=resourceMonitor,
            scriptText=scriptText,
            scriptEstimate=scriptEstimate,
            voiceChoice=voiceChoice,
            repeatButton=repeatButton,
            styleChoice=styleChoice,
            speed=speed,
            referencePreview=referencePreview,
            referenceUpload=referenceUpload,
            voiceConsent=voiceConsent,
            expressiveness=expressiveness,
            temperature=temperature,
            cfg=cfg,
            seed=seed,
            generateButton=generateButton,
            cancelButton=cancelButton,
            status=status,
            fullAudio=fullAudio,
            generationHistory=generationHistory,
            segmentChoice=segmentChoice,
            segmentAudio=segmentAudio,
            regenerateButton=regenerateButton,
            mp3=mp3,
            loadButton=loadButton,
            refreshButton=refreshButton,
            voiceReferences=voiceReferences,
        )
        connectEvents(elements, demo)
    return demo
