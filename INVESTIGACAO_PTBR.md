# Checkpoint especializado em português brasileiro

Consulta realizada em 27/10/2026 às fontes oficiais da Resemble AI. O motor ativo deste projeto é o **Multilingual V3 geral**.

A [ficha oficial PT-BR](https://huggingface.co/ResembleAI/Chatterbox-Multilingual-pt-br) descreve um finetune especializado com `language_id="pt"`. Seus componentes incluem `t3_pt_br.safetensors`, `s3gen_v3.pt` / `s3gen_v3.safetensors` e o tokenizador `grapheme_mtl_merged_expanded_v1.json`.

O [demo oficial](https://huggingface.co/spaces/ResembleAI/Chatterbox-Multilingual-TTS-pt-br/tree/main) **não usa diretamente** o `chatterbox.tts.ChatterboxTTS` inglês do pacote instalado. Ele importa uma implementação própria em `chatterbox/src/chatterbox/tts.py` dentro do Space. A sugestão automática de uso exibida pelo Hugging Face não substitui essas instruções específicas.

O carregador desse demo:

1. Obtém `ve.pt`, `conds.pt` e o tokenizador do repositório base `ResembleAI/chatterbox`.
2. Obtém `t3_pt_br.safetensors` e `s3gen_v3.pt` do repositório `ResembleAI/Chatterbox-Multilingual-pt-br`.
3. Constrói `T3ConfigMultilingual`, com vocabulário de texto de 2.454 e de fala de 8.194 tokens.
4. Carrega o T3 específico e instancia o S3Gen do código desse demo, carregando o decodificador específico `s3gen_v3.pt` (`strict=False` no demo).
5. Prepara a referência e gera com `language_id="pt"`.

As cópias de leitura do `app.py`, do carregador e do inventário do Space estão em `logs/ptbr_*`. Não são importadas nem executadas pela aplicação.

O carregador geral instalado usa `T3Config.multilingual()` e o arquivo **`s3gen.pt`**, e não oferece um argumento para selecionar esse conjunto completo de componentes específicos. A coincidência de tamanhos dos embeddings não confirma a compatibilidade do decodificador. O código do Space também possui uma versão própria dos módulos internos.

**Decisão:** não adaptar nomes de arquivos, não usar `strict=False` para esconder incompatibilidades e não carregar o checkpoint PT-BR como se fosse intercambiável. Não foram baixados seus pesos nem realizados testes de síntese com ele. Integrá-lo corretamente requer um adaptador separado com revisão dos módulos e validação real do estado do decodificador, do áudio e do consumo de memória. Não é necessário para usar o V3 geral já previsto neste projeto.
