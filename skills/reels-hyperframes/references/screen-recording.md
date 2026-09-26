# Modo tela (vídeo sem pessoa aparecendo)

Para gravação de tela narrada, slides ou tutoriais. Não existe pessoa para recortar, então nada passa
"por trás" de ninguém: os efeitos entram **por cima** da tela, e o foco é mostrar bem a parte da tela
que importa. Confirme com a pessoa antes de seguir (a skill foi pensada para quem aparece falando).

## O que muda no passo a passo

1. **Escolha do trecho** (passo 3): igual — gancho, ideia completa, algo concreto. Olhe os quadros do
   trecho (`frames.py range`) para ver o que a tela mostra enquanto a pessoa fala.

2. **Região da tela** (no lugar do passo 4): com `frames.py grid --at ...` em alguns tempos do trecho,
   escolha um retângulo **em pé** (proporção ~9:16) em volta do que interessa. Exemplo numa tela
   1920×1080: `732,70,568,1010` (x, y, largura, altura).
   - **Deixe de fora**: barra de menu do sistema, notificações, agenda, abas, dock, nomes e e-mails.
     Um y ≥ 70 costuma tirar a barra de menu do Mac.
   - Se o conteúdo muda de lugar no trecho, prefira um retângulo que funcione para o trecho inteiro.

3. **Corte** (passo 5) com `--crop` e `--screen`:
   ```bash
   python3 "$SKILL_DIR/scripts/make_clip.py" "$WORK" --pieces "692.43-699.44,744.50-751.95" --crop 732,70,568,1010 --screen
   ```
   O `--screen` cria `plate.webm` (o próprio vídeo) e um `person.webm` transparente.
   **Pule o remove-background** (passo 6): numa tela ele recorta pedaços aleatórios (rostos de miniaturas,
   mãos, produtos) e estraga as camadas.

4. **Efeitos** (passo 8) que funcionam bem por cima de tela:
   - `glass`: as camadas de vidro giram com a tela no fundo e o cartão no meio — ótimo para a ideia central;
   - `bigWord` com `top` alto e `color` escuro em tela clara (ex.: `"#111111"` com `glow` dourado);
   - `frame`: a tela vai para a moldura e os cartões resumem o que ela fala (ex.: 3 benefícios com `"good"`);
   - `bigSymbol` ("$", "!", "?") numa área vazia da tela;
   - socos de câmera em palavras de impacto.
   Evite `bubbles` e `ring` "por trás" (sem pessoa, não há o que ficar na frente) — se usar, trate como
   elemento por cima e posicione numa área vazia.

5. **Posições**: nada de "zona da cabeça"; o cuidado agora é **não cobrir o que a tela mostra**. Ponha
   textos gigantes e cartões em áreas vazias (topo, laterais brancas) e confira no snapshot.

6. **Legendas**: continuam em y ≈ 1250–1340. Se a parte importante da tela estiver ali, mude o recorte
   (outro `--crop`) em vez de mover a legenda.

7. **Render** (passo 11) com `--video-frame-format png` para o texto da interface ficar nítido.

8. **Check** (passo 9): o aviso de contraste das legendas em fundo branco pode ser ignorado (elas têm
   contorno preto).
