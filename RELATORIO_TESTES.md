# Relatório de instalação e testes

Execução real no computador Windows do usuário em **27/10/2026**, horário de São Paulo. Projeto em `C:\Users\kaua9\OneDrive\Documentos\narrador`.

## Instalação confirmada

Python 3.11.9 na `.venv`; Chatterbox oficial 0.1.7, commit `5de7a54aa4e5e2baadb0182dde554908b48b85c2`; PyTorch/Torchaudio 2.6.0+cu126; CUDA runtime 12.6; Gradio 6.8.0; psutil 7.2.2; FFmpeg 9.0 já existente. Demais versões em `requirements-lock.txt`.

Modelo: **Chatterbox Multilingual V3 geral**, idioma `pt`. Pesos oficiais `ResembleAI/chatterbox`, revisão `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18`. Os seis arquivos principais, o dicionário auxiliar e os arquivos do segmentador estão locais e com hashes registrados em `models/modelo.json`.

Não foi necessária instalação como administrador, alteração de driver, do Python global ou de proteções do Windows. Não há dependência obrigatória pendente de instalação manual.

## Resultados efetivamente executados

| Teste | Resultado / evidência |
|---|---|
| Reconhecimento CUDA | **Passou**. `torch.cuda.is_available() == True`; RTX 3050 Laptop de 6 GB; `logs/ambiente.json`. |
| Carregamento pela API solicitada | **Passou**. `ChatterboxMultilingualTTS.from_pretrained(device="cuda", t3_model="v3")`; 53,59 s no primeiro carregamento medido. |
| Frase solicitada em português | **Passou**. `outputs/teste_inicial.wav`, mono, 24 kHz, PCM 16 bits, 7,52 s. Geração inicial em 94,58 s; pico de VRAM alocada 3,17 GiB. |
| Referências de voz | **Passou**. Os 15 OGG foram lidos pelo FFprobe e convertidos em cópias de até 10 s. Geração real com `audio1.ogg`; cancelamento com `audio2.ogg`. Os demais estão cadastrados, mas não foram todos usados em sínteses individuais. |
| Segmentação e geração sequencial | **Passou**. Roteiro real em três segmentos, com a frase solicitada e duas frases adicionais; projeto `20261027-121107-56000e`. |
| União e normalização | **Passou**. Exportação completa, com pausas e volume ajustado, 15,896625 s a 1,1×. |
| WAV e MP3 reais | **Passou**. `outputs/exemplo_com_referencia.wav` e `.mp3`; arquivos também baixados pelo endpoint local no teste de integração HTTP. |
| Velocidade preservando tom | **Passou**. Teste com tom de 220 Hz verificou frequência preservada e duração próxima à razão 1,1×. O exemplo real também usa `ffmpeg atempo=1.1`. |
| Regeneração de um segmento | **Passou**. Segmento 2 regenerado; nomes e SHA-256 dos segmentos 1 e 3 permaneceram idênticos. O take anterior do segmento 2 foi preservado. |
| Funcionamento offline | **Passou**. Os processos de geração da integração e da regeneração bloquearam conexões de socket; carregamento, referência, síntese e exportação funcionaram. A rede do Windows não foi alterada. |
| Exclusão de gerações simultâneas | **Passou**. Segunda tarefa no mesmo controlador foi rejeitada enquanto havia uma tarefa ativa. A interface também limita a concorrência da GPU a uma tarefa. |
| Cancelamento com preservação de segmentos | **Passou**. Cancelamento durante o segundo segmento preservou o primeiro no projeto `20261027-121454-5e65c8`. |
| Cancelamento e fim dos processos | **Passou**. Teste adicional durante inferência, projeto `20261027-121801-abd662`, confirmou que os três processos descendentes identificados foram encerrados. `nvidia-smi` mostrou **0 MiB** de uso da GPU depois do teste. |
| Integridade dos pesos e auxiliares | **Passou**. `scripts/verificar.py --hashes` executado após preparar todos os recursos. |
| Compatibilidade das dependências | **Passou**. `pip check`: `No broken requirements found`. |
| Testes automatizados de texto e áudio | **5/5 passaram**. Incluem abreviações, parágrafos, preservação das palavras, entrada longa, união, volume, WAV/MP3 e tom a 1,1×. |
| Arquivo `iniciar.bat` | **Passou** na verificação de ambiente e no início real do servidor. Foi executado normalmente e novamente com `--sem-navegador` para testar a versão final. Nenhuma instalação ou download foi solicitado no início. |
| Servidor local e interface | **Passou na integração HTTP**. HTTP 200, 53 componentes, carregamento do histórico pela fila real, seleção do áudio do segmento e download dos arquivos. Socket de escuta confirmado somente em **127.0.0.1:7860**. Telemetria desativada e nenhum endpoint marcado como API pública. |
| Conferência visual no navegador | **Não realizada**. A ferramenta de controle visual foi interrompida porque não conseguiu confirmar a URL atual no Windows. Não houve tentativa de contornar essa interrupção. |
| Geração real de dez minutos | **Não executada**. A suíte verificou a segmentação de 1.500 palavras nos seis estilos, sem perda de texto. Não foi medida uma geração contínua real de dez minutos. |
| Falta real de memória CUDA | **Não provocada**. O tratamento existe, mas não se forçou esgotamento da GPU. |
| Checkpoint especializado PT-BR | **Somente investigado**. Não baixado, integrado ou testado em síntese; ver `INVESTIGACAO_PTBR.md`. |

A integração completa com referência, três segmentos, regeneração e cancelamento levou **334,6 s**. O maior pico de VRAM registrado nessa integração foi **3,439 GiB** de memória alocada pelo PyTorch, sem contar possíveis reservas adicionais do driver. A inferência normal habilita TF32 para a arquitetura Ampere. Esses tempos não constituem garantia de desempenho para todos os textos; a primeira execução também prepara caches e pode ser mais lenta.

Os áudios foram gerados e suas propriedades técnicas verificadas. **Não foi feita avaliação auditiva subjetiva** da pronúncia, interpretação ou semelhança vocal. Ouça os exemplos antes de usar a voz em produção.

## Problemas encontrados e soluções

1. **Python padrão diferente do solicitado:** o comando `python` global apontava para Python 3.13. A `.venv` foi criada explicitamente com `py -3.11`; toda a instalação ficou isolada.
2. **Pacotes CUDA grandes e extração lenta no Windows:** instalados os binários oficiais CUDA 12.6 compatíveis com a versão 2.6.0 exigida pelo projeto. Não se instalou o CUDA Toolkit global nem se alterou o driver existente.
3. **Downloads auxiliares ocultos no tokenizador:** a primeira carga oficial baixou o modelo `spacy_ontonotes` de `explosion/spacy-pkuseg` para `C:\Users\kaua9\.pkuseg`. Os arquivos foram copiados para `.cache/pkuseg` e `PKUSEG_HOME` passou a apontar para o projeto. O script de preparação agora baixa explicitamente esse recurso da fonte oficial e registra seus hashes. A cópia inicial externa foi preservada; não é usada pela aplicação configurada.
4. **Cache separado do dicionário Cangjie:** o código oficial solicita um cache dentro da pasta do checkpoint. Esse cache também foi preparado e verificado para a execução offline, além do arquivo principal.
5. **Mudança da API do Gradio 6:** configurados `api_visibility="private"`, tema/CSS na inicialização e tradução dos controles internos usando o bundle local da versão 6.8.0 fixada. O servidor e seus callbacks passaram nos testes HTTP; a aparência e a execução da tradução no navegador ainda precisam de conferência visual.
6. **Cancelamento no Windows:** o controlador encerra a árvore exclusiva da tarefa, incluindo os executáveis filhos do Python da `.venv`, sem encerrar outros aplicativos do usuário. O teste adicional confirmou ausência de processos restantes.
7. **Saída de progresso em stderr:** o PowerShell classificou as barras do download como mensagens de erro e retornou status 1 em uma execução com redirecionamento, apesar do download concluído. Uma nova execução direta terminou com código 0 e os hashes foram verificados. Nenhum erro de download ficou pendente.

## Evidências locais

- `logs/ambiente.json`
- `logs/teste_inicial.json`
- `logs/teste_integracao.json`
- `logs/teste_cancelamento.json`
- `logs/teste_interface.json`
- `logs/instalacao_pip.log` e `logs/instalacao_psutil.log`
- `outputs/*/projeto.json` e logs individuais das tarefas.

O servidor de teste foi encerrado ao concluir a entrega. Abra `iniciar.bat` para iniciar uma sessão normal com sua própria janela de console.

## Correção do início com uma instância já aberta — 27/10/2026

A refatoração visual havia deixado uma leitura do byte zero de `.app.lock` antes da aquisição do bloqueio. No Windows, uma segunda execução podia falhar nessa leitura com `PermissionError`, antes de reconhecer a instância existente.

O bloqueio foi separado em `narrador/instance.py` e não lê nem escreve o byte reservado. A segunda execução agora trata o bloqueio como uma instância já aberta e reabre o servidor local quando ele se identifica como o Narrador. O motor de geração não foi modificado.

Três regressões reais entre processos Windows passaram: bloqueio de arquivo vazio, identificação de byte já bloqueado por outro processo e liberação do bloqueio após exceção. Junto aos testes anteriores, a suíte teve **8 testes aprovados**. Uma segunda execução real de `app.py --sem-navegador` também terminou com código zero e a mensagem de que o Narrador já estava aberto.

## Correção visual de alinhamento — 27/10/2026

Após as capturas de sobreposição enviadas pelo usuário, os agrupamentos compactos foram substituídos por colunas e o CSS foi corrigido para o DOM da versão instalada do Gradio. A validação visual real foi concluída em Chrome isolado com sandbox ativo e requisições limitadas à prévia local, em 320, 390, 768, 1024 e 1440 pixels.

As cinco larguras passaram nas verificações de ausência de overflow horizontal, distância entre roteiro e estimativa, altura dos inputs de todos os sliders, fundos transparentes dos Forms e posicionamento das colunas. Imagens foram examinadas, incluindo os ajustes avançados abertos em celular. A suíte existente continuou com **8 testes aprovados** e os arquivos do motor permaneceram idênticos por SHA-256. As evidências estão em `logs/teste_alinhamento.json` e nas capturas `logs/layout-*.png` / `logs/ajustes-*.png`.
