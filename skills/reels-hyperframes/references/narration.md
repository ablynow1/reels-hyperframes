# Narração com voz gerada (motor da Microsoft)

Para vídeo sem fala (gravação de tela muda, produto, animação), áudio ruim, ou quando a pessoa pede uma
versão narrada. A voz sai do motor de voz da Microsoft (o mesmo da leitura em voz alta do Edge), pelo
`narrate.py`. **Quem escolhe a voz é a pessoa.**

Não use o `npx hyperframes tts` (modelo Kokoro) nem o `say` do Mac: em português eles soam robóticos. Foi
isso que fez gente refazer a narração no CapCut e ressincronizar o vídeo à mão.

## Passo a passo

1. **Roteiro.** Escreva com a pessoa (ou a partir da transcrição) e confirme o texto antes. As regras da
   skill continuam valendo: nada de número, promessa ou nome que a pessoa não aprovou. Escreva do jeito que
   se fala:
   - números por extenso ("noventa por cento");
   - palavra estrangeira como se pronuncia, se sair errada (o motor leu "gateways" como "gatevais"):
     "guêituêis";
   - siglas com hífen ou separadas, se precisar soletrar.
   Tamanho: ~2,5 palavras por segundo (15 s ≈ 35 a 40 palavras).
2. **Vozes.** `python3 "$SKILL_DIR/scripts/narrate.py" --list` mostra as vozes do português do Brasil
   (Antonio, Francisca, Thalita). Com `--all` aparecem também as vozes "Multilingual" de outros países, que
   falam português com sotaque.
3. **Amostras.** `python3 "$SKILL_DIR/scripts/narrate.py" "$WORK" --samples --script roteiro.txt` gera uma
   amostra de cada voz, com a 1ª frase do roteiro, em `source/vozes/`. Mande para a pessoa ouvir e **espere
   ela escolher**. Não escolha por ela.
4. **Corte.** `make_clip.py` com um trecho de vídeo pelo menos do tamanho da narração (no modo tela,
   `--screen`). Vídeo com a pessoa falando para a câmera não combina com voz por cima (a boca fica fora de
   sincronia): prefira tela, produto, b-roll ou cenas sem fala.
5. **Narração.**
   ```bash
   python3 "$SKILL_DIR/scripts/narrate.py" "$WORK" --voice pt-BR-FranciscaNeural --script roteiro.txt
   ```
   Gera `assets/voice.m4a` (a voz do vídeo, com o volume padrão da skill) e `narration.json` (o tempo de
   cada palavra). A voz original do corte fica em `assets/voice_original.m4a`, e o vídeo passa a ter o
   tamanho da narração. `--rate +10%` acelera; `--pitch -2Hz` engrossa a voz.
6. **Legendas.** `build_captions.py` usa a narração sozinho: as palavras vêm do roteiro e os tempos são
   exatos, sem Whisper e sem ressincronizar. Revise só os destaques.
7. **Daqui em diante, igual.** Tire os tempos dos efeitos do `narration.json` (ex.: o soco de câmera no
   início da palavra "Appmax") e siga com build, check, review e render.

Para voltar à voz original, rode o `make_clip.py` de novo: ele refaz a voz e o `clip.json`, e a narração
deixa de valer.

## Bom saber

- Precisa de internet e de `pip3 install edge-tts`. Se parar de funcionar (erro 403 ou "No audio was
  received"), atualize: `pip3 install -U edge-tts`.
- **Uso comercial:** o edge-tts usa o serviço de leitura do Edge, que a Microsoft não licencia oficialmente
  para uso comercial. Para anúncio pago, as mesmas vozes estão no Azure AI Speech, que é o caminho oficial
  (500 mil caracteres por mês grátis). Avise a pessoa na entrega.
