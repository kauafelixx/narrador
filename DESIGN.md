# Direção visual da interface

Brief: laranja e branco, Montserrat, formas arredondadas, boa usabilidade e nenhuma mudança no motor de geração.

## Sistema visual

- Branco `#FFFFFF`: áreas de trabalho e campos.
- Cinza claro `#F7F8FA`: fundo da página.
- Grafite `#263241`: texto principal.
- Cinza `#667180`: texto de apoio.
- Laranja `#C94A0A`: ação principal e foco; contraste com texto branco.
- Laranja suave `#FFF3E8`: seleção e apoio à identidade.

Montserrat variável local, pesos 400–750. Título de página 32 px, seções 19 px, corpo 14–16 px, apoio 12–13 px. Texto do roteiro com 16 px e entrelinha 1,7. Conteúdo alinhado à esquerda.

## Organização

Uma mesa de narração: editor amplo à esquerda, reprodução à direita. Histórico e segmentos compartilham a coluna de resultado por abas. Opções avançadas ficam em seções expansíveis, mantendo o primeiro uso simples.

```text
[ marca circular / Narrador                    processamento local ]
[ Dê voz ao seu roteiro.                                          ]
[ Roteiro e interpretação            ][ Resultado | Histórico | Segmentos ]
[ texto                              ][ progresso / player                 ]
[ voz / estilo / velocidade           ][ WAV / MP3                          ]
[ ajustes opcionais                   ][                                    ]
[ Gerar narração          Cancelar    ][                                    ]
[ segmentos do roteiro, expansível                                         ]
[ desempenho, expansível                                                  ]
```

Em telas estreitas, a saída passa para baixo do editor. Campos e botões respeitam a largura disponível; nenhum tamanho mínimo deve forçar rolagem horizontal. Controles clicáveis têm pelo menos 44 px de altura; foco de teclado visível; sem animação automática.

## Revisão antes da implementação

O pedido de formas circulares será aplicado à marca, ao player e aos botões. Campos terão raio menor para continuar parecendo editáveis. Não serão usadas grades de cartões idênticos, gradientes, grandes áreas decorativas nem um cabeçalho que ocupe espaço excessivo. O detalhe característico será uma onda sonora dentro da marca circular. A página usa o conteúdo real de narração e mantém a ação principal junto ao roteiro.

## Validação

Verificar a inicialização do Gradio, o carregamento local da fonte, os callbacks de histórico/segmentos e a entrega dos arquivos. Revisar desktop e tela estreita visualmente quando a ferramenta de navegador permitir. Registrar com precisão qualquer limite de verificação visual.

Implementação: camadas de view, elementos tipados, eventos, actions e tema em `narrador/interface`; estilos separados em `assets/styles`; funções e variáveis da interface em camelCase. A paleta clara também é aplicada quando o navegador está configurado para modo escuro. Conforme o ajuste solicitado, os painéis principais têm borda mais definida e sombra suave, e roteiro e interpretação possuem grupos próprios. O motor de áudio foi preservado byte por byte e seus formatos de entrada/saída permanecem os mesmos.

Validação inicial do redesenho: análise estática com Ruff, construção dos 62 componentes daquela versão, callbacks reais de histórico e seleção de segmentos pela fila do Gradio, downloads WAV/MP3 e entrega local da Montserrat. Naquela etapa, a captura automática de desktop e mobile foi rejeitada pela revisão de execução com a mensagem `blocked by policy`, e a conferência visual permaneceu pendente. A validação visual posterior está registrada abaixo.

## Correção de alinhamento — 27/10/2026

As capturas do usuário revelaram compactação de `gr.Group`, fundos dos Forms automáticos, números de sliders recortados e seletores de abas incompatíveis com Gradio 6.8. Os blocos de roteiro e interpretação passaram a usar `Column`; estilo e velocidade têm colunas próprias; Forms são transparentes e espaçados apenas dentro dos painéis da interface. As alturas dos inputs numéricos respeitam os seus contêineres, os rótulos preservam palavras inteiras e as margens negativas foram removidas.

As abas usam seletores semânticos `role="tab"` e `role="tablist"`. O espaço externo usa `clamp`, evitando a reescrita incorreta dos seletores da raiz em media queries pelo Gradio. Cabeçalho e downloads vazios também foram ajustados.

A revisão de execução autorizou novos testes isolados da prévia local. Foi possível concluir a validação real em Chrome com sandbox ativo, nas larguras de **320, 390, 768, 1024 e 1440 px**, com os painéis de referência e ajustes avançados abertos. Em todas: sem overflow horizontal, sem sobreposição da estimativa com o roteiro, inputs numéricos inteiros e reorganização das colunas nas telas menores. A Montserrat local foi carregada. Medidas em `logs/teste_alinhamento.json`; imagens em `logs/layout-<largura>.png` e `logs/ajustes-<largura>.png`.

Os testes de desenvolvimento e suas dependências ficam isolados em `.cache`, sem alterar as dependências de execução do narrador ou os arquivos do motor de áudio.
