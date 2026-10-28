# Narrador local — Chatterbox Multilingual V3

Ferramenta de narração em português, executada no Windows com Gradio e a GPU NVIDIA.
Pasta: `C:\Users\kaua9\OneDrive\Documentos\narrador`.

## Iniciar e encerrar

1. Dê dois cliques em **iniciar.bat**.
2. Aguarde a verificação local. O navegador abre em **http://127.0.0.1:7860**.
3. Escolha a referência de voz, cole o roteiro, escolha o estilo e clique em **Gerar narração**.
4. Ouça o resultado e baixe o MP3. Tudo também fica em `outputs`.
5. Para encerrar, pressione **Ctrl+C** na janela do programa. Confirme o encerramento do lote se o Windows perguntar. Fechar a aba do navegador não encerra o servidor.

Se você abrir `iniciar.bat` novamente enquanto o aplicativo já estiver rodando, a nova execução reconhece a instância existente e reabre seu endereço no navegador, sem iniciar outra geração ou mostrar uma falha de inicialização. O controle de instância única fica em `narrador/instance.py`.

O início normal não instala pacotes nem baixa modelos. A interface escuta somente em `127.0.0.1`; `share=False` impede a criação de um endereço público pelo Gradio. Não é necessária conta, API paga ou cota mensal. A geração usa energia, espaço em disco e tempo da GPU local.

## Interface e organização do código

A interface usa laranja e branco, Montserrat armazenada em `assets/fonts` e controles arredondados. O roteiro e os ajustes principais ficam na área de edição; a saída tem as abas **Resultado**, **Histórico** e **Segmentos**. As referências adicionais, os ajustes avançados e o monitor de desempenho podem ser expandidos quando necessários. O CSS empilha as colunas em telas de até 800 px e reorganiza os controles em telas menores.

O ponto de entrada `app.py` prepara o ambiente offline; `narrador/launcher.py` inicia e encerra o servidor. A camada visual está separada em:

- `narrador/interface/view.py`: composição da página.
- `narrador/interface/elements.py`: referências tipadas aos controles.
- `narrador/interface/events.py`: ligações entre controles e callbacks.
- `narrador/interface/actions.py`: apresentação dos resultados e encaminhamento das ações ao controlador.
- `narrador/interface/theme.py`: tema, idioma e carregamento dos estilos locais.
- `assets/styles/base.css`: fonte, cores e acessibilidade.
- `assets/styles/layout.css`: estrutura da página e do editor.
- `assets/styles/controls.css`: campos, botões, abas e players.
- `assets/styles/responsive.css`: ajustes para diferentes larguras e preferência de movimento reduzido.

As funções e variáveis novas da camada visual seguem camelCase. Os nomes exigidos pelas APIs externas e os formatos dos projetos salvos são preservados. Os arquivos do controlador, do worker, do processamento de áudio e da segmentação não foram modificados durante o redesenho.

## Modelo e ambiente

- Python 3.11.9, isolado em `.venv`.
- Chatterbox oficial: `chatterbox-tts 0.1.7`, checkout `5de7a54aa4e5e2baadb0182dde554908b48b85c2`, subpasta `chatterbox`.
- Motor: **Chatterbox Multilingual V3**, `t3_model="v3"`, `language_id="pt"`.
- PyTorch e Torchaudio **2.6.0+cu126**. O runtime CUDA 12.6 vem no pacote; não é necessário instalar o CUDA Toolkit global.
- GPU detectada: NVIDIA GeForce RTX 3050 6GB Laptop GPU. Driver existente: 591.59.
- RAM detectada: aproximadamente 15,7 GB. CPU configurada para quatro threads nas tarefas de inferência.
- A inferência usa TF32 para acelerar multiplicações FP32 na arquitetura Ampere da RTX 3050.
- Gradio 6.8.0 e demais versões exigidas pelo `pyproject.toml` oficial. `psutil` monitora RAM.
- FFmpeg existente no computador permite exportação MP3 e velocidade com preservação de tom.
- Dependências e pesos são obtidos de PyPI, do índice oficial do PyTorch e dos repositórios oficiais Resemble AI. Nenhum Python global, driver ou configuração do Windows é alterado pela aplicação.

Os pesos e a revisão do Hugging Face ficam registrados em `models/modelo.json`, incluindo tamanho e SHA-256 de cada arquivo. O cache fica em `.cache/huggingface`, dentro deste projeto. O código do motor é mantido no checkout oficial; a interface e o processamento estão no pacote `narrador`.

O tokenizador oficial também inicializa componentes auxiliares para outros idiomas. O recurso PKUSEG foi preparado em `.cache/pkuseg`, e o dicionário Cangjie foi armazenado no cache adicional usado pelo carregador. Ambos são verificados para permitir uso offline. A primeira carga oficial criou uma cópia em `C:\Users\kaua9\.pkuseg`; ela foi preservada e não é usada pela configuração final.

## Vozes de referência

O catálogo ativo foi substituído por **audio-novo.mp3**, enviado em 28/10/2026. Uma cópia integral, com SHA-256 registrado em `references/catalogo.json`, fica em `references`; o original em Downloads permanece intacto. As referências antigas deixaram de aparecer na lista. Projetos antigos conservam suas próprias amostras.

**audio-novo.mp3** é a seleção inicial. Ouça a prévia ou envie outra referência pela interface; esse arquivo tem prioridade sobre a lista. Escolher **Voz padrão do modelo** e deixar o envio vazio usa a voz interna do checkpoint.

Use fala limpa em português brasileiro, sem música ou outras pessoas, com pelo menos três segundos. A preparação retira silêncio inicial, preserva até dez segundos em FLAC de 24 bits e aplica somente ganho constante, sem compressor nem filtro de timbre. A amostra nova fornece a identidade vocal e o sotaque; não existe um controle independente para remover o R regional. A semelhança precisa ser conferida ouvindo o resultado. A confirmação de autorização deve permanecer marcada somente para áudios próprios ou autorizados.

Cada projeto salva a referência usada. Regenerar um segmento mantém essa referência para preservar a identidade vocal. Para trocar a referência de toda a narração, gere o roteiro inteiro novamente.

## Interpretação e velocidade

Os nomes dos estilos são sugestões de ajustes, não comandos emocionais do modelo. Não são inseridas tags de emoção ou parâmetros inexistentes.

| Estilo | Expressividade | Temperatura | CFG | Máx. caracteres/trecho | Pausa entre frases / parágrafos |
|---|---:|---:|---:|---:|---:|
| Natural | 0,60 | 0,75 | 0,35 | 280 | 0,22 / 0,55 s |
| Solene | 0,45 | 0,70 | 0,35 | 240 | 0,36 / 0,80 s |
| Emocionante | 0,70 | 0,85 | 0,35 | 240 | 0,28 / 0,65 s |
| Dramático | 0,80 | 0,85 | 0,30 | 220 | 0,40 / 0,85 s |
| Suspense | 0,60 | 0,70 | 0,30 | 220 | 0,48 / 0,95 s |
| Energético | 0,75 | 0,90 | 0,45 | 260 | 0,16 / 0,40 s |

Expressividade aumenta a intensidade; temperatura aumenta a variação; CFG influencia o condicionamento. Perguntas e exclamações conservam a pontuação na entrada do modelo e recebem um aumento moderado de intensidade, de 0,03 e 0,08, respectivamente, limitado ao máximo do controle. Pausas variam com perguntas, exclamações e reticências. Não são inseridas tags de emoção. A reação é probabilística e depende da voz e do texto. Confira o áudio e regenere trechos quando necessário.

Anos com contexto, como **no ano de 1830** e **em 1830**, são enviados à síntese como **mil oitocentos e trinta**. Datas válidas como **28/10/2026**, **28-10-2026** e **2026-10-28** recebem dia, mês e ano por extenso. Datas com pontos exigem o rótulo “dia” ou “data” para não confundir versões. O roteiro exibido permanece original; cada segmento salva também `texto_fala`. Números isolados, códigos, telefones e datas inválidas não são reinterpretados como datas. Acentos são preservados em Unicode NFC.

O controle **Velocidade** inclui **1,10**. O processamento usa `ffmpeg atempo`, que altera a duração preservando o tom, na mesma etapa da exportação MP3 V0. FFmpeg é obrigatório e sua instalação WinGet também é procurada quando o PATH do aplicativo está desatualizado. A semente 0 escolhe uma nova variação; a semente efetiva é salva no projeto. Reprodutibilidade absoluta entre diferentes GPUs/versões não é garantida.

## Roteiros longos, histórico e segmentos

A aplicação suporta roteiros da ordem de dez minutos por meio de processamento sequencial. O limite de entrada é 2.000 palavras e 30.000 caracteres. A estimativa usa 150 palavras por minuto; o tempo real depende da voz, das pausas e da velocidade. Não há corte forçado do áudio em dez minutos.

- Frases e parágrafos são preservados. Frases muito longas são divididas em vírgulas, ponto e vírgula, dois-pontos ou espaços.
- Abreviações comuns e números decimais são protegidos. O texto completo nunca é passado ao modelo de uma vez.
- Um segmento é gerado por vez. Cada take é salvo imediatamente em WAV PCM de 24 bits e 24 kHz.
- A montagem remove apenas silêncio nas bordas, conserva uma margem e insere pausas entre frases e parágrafos.
- A montagem inteira recebe ganho constante visando -18 LUFS, limitado a ±8 dB, com margem para picos da codificação. Isso preserva o contraste de volume entre falas e não comprime a interpretação; não é uma garantia de loudness final exato.
- A exportação completa produz **somente MP3 VBR V0**, diretamente das amostras float32. Não são criados WAV base nem WAV final, e não há recodificação intermediária do MP3. Os takes internos WAV de 24 bits são preservados para edição e regeneração.
- Escolha uma geração no histórico e clique em **Carregar geração**. Selecione um segmento para ouvi-lo ou regenerá-lo com os ajustes atuais. Os outros trechos permanecem e a montagem é refeita.
- A regeneração de um trecho conserva a divisão e as pausas originais do projeto; alterar o estilo e gerar o roteiro inteiro aplica uma nova segmentação e novas pausas.
- Se uma tarefa for cancelada, o histórico conserva os trechos prontos. Regere os pendentes um por vez, ou gere novamente o roteiro inteiro. A exportação completa aparece quando todos os segmentos estão disponíveis.
- Takes e exportações anteriores são mantidos. Isso ocupa espaço; remova manualmente as pastas de projetos que não quiser conservar, com o aplicativo encerrado.

Estrutura de uma geração:

```text
outputs/AAAAMMDD-HHMMSS-identificador/
  projeto.json                # texto, parâmetros, semente, duração e estado
  referencia.flac             # referência desse projeto, quando usada
  segmento_0001_<take>.wav     # cada trecho e seus takes
  narracao_<versao>.mp3
```

## Cancelamento, memória e erros

Somente uma tarefa de geração roda por vez. A interface usa uma fila limitada e um bloqueio do controlador. Um bloqueio de arquivo impede duas instâncias da interface neste projeto.

O modelo fica em um processo filho exclusivo. **Cancelar geração** encerra esse processo, preserva os arquivos já salvos e devolve a memória CUDA ao sistema. Cada nova tarefa carrega novamente o modelo: há um pequeno custo de carregamento, em troca de liberar a GPU após a tarefa e de permitir cancelamento imediato durante uma frase. O limite do alocador CUDA é 90% da VRAM para reduzir a disputa com o Windows. Não há tentativas automáticas indefinidas após falhas.

O uso de RAM, VRAM, GPU e temperatura aparece na interface. Em caso de memória CUDA insuficiente, a tarefa é interrompida com mensagem em português. Feche jogos e outros aplicativos que usam a GPU e tente um texto mais curto. Se um segmento não apresentar avanço durante dez minutos de processamento, o controlador encerra a tarefa. Não se deve esperar que dez minutos de áudio sejam gerados em dez minutos de relógio.

Consulte `logs/interface.log` e `logs/<identificador>.log` para falhas. Textos e caminhos podem aparecer nesses logs locais.

## Uso offline e privacidade

Após o download explícito dos pesos, a aplicação força `HF_HUB_OFFLINE=1` e `TRANSFORMERS_OFFLINE=1`. Usa `from_local(..., t3_model="v3")` para o funcionamento normal. O teste inicial também verifica a API oficial `from_pretrained(device="cuda", t3_model="v3")`.

Telemetria de Hugging Face e Gradio é desabilitada no processo. A interface usa fontes do sistema. Textos, referências e áudios não são enviados a serviços externos pela aplicação. O Gradio recebe arquivos apenas pelo servidor local. A primeira instalação e o script de download precisam de internet; o início normal não precisa.

**A pasta solicitada está dentro do OneDrive.** A aplicação não controla a sincronização já configurada no Windows. Caso o OneDrive sincronize esta pasta, seus textos e áudios locais poderão ser copiados por ele. Para armazenamento estritamente fora da nuvem, use uma pasta fora do OneDrive e recrie a `.venv` nela com as instruções abaixo; não mova uma `.venv` existente, pois seus caminhos internos podem ser absolutos. Nenhuma configuração do OneDrive foi alterada.

O watermarker Perth oficial é mantido. A aplicação não o desativa.

## Testes e diagnóstico

Os resultados reais da sessão são registrados em **RELATORIO_TESTES.md**. Os arquivos JSON em `logs` guardam medidas do hardware e das gerações. Não considere um teste concluído apenas porque o código correspondente existe.

O exemplo atualizado com a nova referência fica em `outputs/exemplo_nova_voz.mp3`. Os scripts de diagnóstico e integração também usam a primeira referência do catálogo e exportam somente MP3. Resultados de testes anteriores não são regravados nem removidos do histórico.

```powershell
.\.venv\Scripts\python.exe scripts\verificar.py --hashes
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\teste_inicial.py --bloquear-rede
```

O teste com `--bloquear-rede` bloqueia conexões de socket no próprio processo, além de ativar os modos offline. Ele não altera firewall, adaptadores de rede nem configurações do Windows. O teste de dez minutos da suíte verifica segmentação com aproximadamente 1.500 palavras; não representa uma geração real de dez minutos. A qualidade artística e a semelhança vocal devem ser avaliadas ouvindo os resultados.

## Instalação e reprodução em outra pasta

Este procedimento é explícito e usa internet. Não é executado pelo `iniciar.bat`.

Pré-requisitos oficiais: [Python 3.11](https://www.python.org/downloads/release/python-3119/), [Git para Windows](https://git-scm.com/downloads/win), [driver NVIDIA](https://www.nvidia.com/Download/index.aspx) e, para MP3, [FFmpeg](https://ffmpeg.org/download.html). No computador verificado, todos estavam disponíveis.

```powershell
py -3.11 -m venv .venv
git clone https://github.com/resemble-ai/chatterbox.git chatterbox
git -C chatterbox checkout 5de7a54aa4e5e2baadb0182dde554908b48b85c2
# Leia chatterbox/README.md e chatterbox/pyproject.toml antes de instalar.
.\.venv\Scripts\python.exe -m pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126
.\.venv\Scripts\python.exe -m pip install -e .\chatterbox
.\.venv\Scripts\python.exe -m pip install -r requirements-local.txt
.\.venv\Scripts\python.exe scripts\baixar_modelo.py
.\.venv\Scripts\python.exe scripts\verificar.py --hashes
```

Copie também `app.py`, `narrador`, `assets`, `scripts`, `iniciar.bat` e, se desejar, `references` para a nova pasta. `requirements-lock.txt` registra as versões efetivamente instaladas nesta sessão. Não é necessário usar administrador ou alterar o Python global. Reserve aproximadamente 15–20 GB para ambiente, caches, pesos e margem para gerações.

## Checkpoint PT-BR especializado

O modelo especializado foi investigado, mas não é selecionável nesta versão. Ele tem `t3_pt_br.safetensors` e **S3Gen V3 próprio**, além de código específico no demo oficial. Não é correto trocar apenas o arquivo T3 do carregador geral. Consulte [INVESTIGACAO_PTBR.md](INVESTIGACAO_PTBR.md) para o procedimento observado e as limitações. A aplicação permanece no Multilingual V3 geral, conforme solicitado.

## Fontes oficiais consultadas

- [Repositório e README Chatterbox](https://github.com/resemble-ai/chatterbox)
- [Dependências oficiais no commit instalado](https://github.com/resemble-ai/chatterbox/blob/5de7a54aa4e5e2baadb0182dde554908b48b85c2/pyproject.toml)
- [Versões e binários oficiais do PyTorch](https://pytorch.org/get-started/previous-versions/)
- [Pesos Multilingual](https://huggingface.co/ResembleAI/chatterbox)
- [Modelo PT-BR especializado](https://huggingface.co/ResembleAI/Chatterbox-Multilingual-pt-br)
- [Código do demo oficial PT-BR](https://huggingface.co/spaces/ResembleAI/Chatterbox-Multilingual-TTS-pt-br/tree/main)
- [Watermarker Perth oficial](https://github.com/resemble-ai/Perth)

