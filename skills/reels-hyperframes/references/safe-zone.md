# Área segura do Reels (tela 1080×1920)

O vídeo é 1080×1920, mas ninguém vê os 1080×1920 inteiros no celular: a interface do Instagram cobre
o topo, a base e a coluna de botões, e em tela mais alta que 9:16 (iPhone 16 é 19,5:9; muitos Android
são 20:9) o Instagram dá zoom para preencher a altura e **corta as laterais**. No iPhone 16 o player
mostra só x ≈ 97–983 (medido no próprio Instagram). Texto nessas faixas fica embaixo da interface ou
some — foi o que aconteceu com o Reels de teste (palavra gigante atrás do cabeçalho, cartões e tabela
cortados na lateral, legenda longa embaixo do botão de curtir).

## Os números (`SAFE_ZONE` em `scripts/common.py`)

| faixa | onde (px) | o que tem lá |
| --- | --- | --- |
| topo | y < 300 | barra de status, Dynamic Island, cabeçalho "Reels" e câmera (≈ 250 px no iPhone 16). No feed o Reels aparece cortado em 4:5, sem os 285 px de cima e de baixo. |
| base | y > 1440 | @ do perfil, botão seguir, legenda do post, música, barra de navegação |
| laterais | x < 120 e x > 960 | corte do zoom em celular alto (~100 px de cada lado) |
| coluna de botões | x > 860 com y > 900 | curtir, comentar, compartilhar, salvar, áudio |
| legendas | y 1170 até ~1290 | faixa das legendas palavra por palavra (os outros textos ficam acima de 1150) |

Ou seja, **texto** pode ficar em x 120–960 (só até 860 abaixo de y 900) e y 300–1150; o anel e o
símbolo gigante (decorativos) podem descer até 1440.

A orientação oficial da Meta para anúncios em Reels deixa livres 14% em cima (~270 px), 35% embaixo
(~670 px, por causa do botão do anúncio) e 6% dos lados (~65 px). Para post orgânico a base pode ser
menor, mas 65 px de lado não bastam no iPhone 16 — por isso aqui a lateral é 120 px.

## O que o modelo faz sozinho

O `template.html` monta a cena depois que as fontes carregam e, antes de o HyperFrames capturar o
primeiro quadro, mede e encaixa cada elemento:

- **legendas**: largura até x 860; bloco um pouco largo desliza para a esquerda, longo diminui a fonte;
- **palavra gigante, balões, símbolo**: diminui a fonte se não couber e empurra para dentro — já
  contando o zoom da câmera enquanto eles estão na tela (no soco o texto vai para os lados e para baixo;
  quando a câmera volta, sobe) e a tremida;
- **cartão das camadas de vidro**: mede a caixa real na tela durante o giro 3D e empurra para dentro
  (como a cena encolhe no giro, `left` ~40 no config já aparece dentro da área);
- **moldura**: manchete no alto da área segura (fonte ajustada à largura), moldura entre x 120 e 960
  e abaixo da manchete, cartões entre a margem e a moldura (encolhem juntos se não couberem);
- **anel**: raio e centro ajustados para o anel inteiro caber, com o zoom;
- **ilustração e tabela**: painel entre y 300 e as legendas; até a altura dos botões usa a largura
  toda (x 120–960), mais alto que isso para antes deles (x 120–860); se não couber, encolhe.

Os ajustes ficam em `window.__safeZone` e no console do navegador; o `build_composition.py` avisa antes
o que vai ser mexido. Se algo não couber nem com a fonte em ~45% (texto comprido demais), o check do
HyperFrames acusa `[área segura] … encurte o texto` — divida a legenda ou encurte a palavra.

## O que continua sendo com você (olhe o `celular.jpg`)

A área segura não sabe onde está a cabeça da pessoa:

- **palavra gigante "por trás"**: agora ela começa em y ≈ 300. Num close (cabeça no alto da tela) a
  cabeça cobre a palavra — use `"front": true` (fica na frente, logo acima das legendas). Config antigo
  com `top` acima de 300 ("acima da cabeça") já vira "na frente" sozinho;
- **balões perto do rosto**: com menos espaço na lateral, uma parte maior do balão fica atrás da
  cabeça. Use largura menor (240–280) ou `"front": true` nos balões;
- **símbolo gigante**: decorativo, pode ficar meio atrás da cabeça, mas confira se ainda dá para ler.

O `review.py` gera `snaps_review/celular.jpg` (e `renders/revisao_celular.jpg` com `--render`): os
mesmos quadros com as faixas vermelhas onde a interface cobre ou o celular corta e uma linha amarela no
topo das legendas. Nada de texto, número ou cartão encostando no vermelho. Para o vídeo inteiro:
`python3 scripts/sheet.py <video> --fps 2 --celular`.

## Outro app ou outra interface

Os números servem para Instagram e ficam perto do Shorts e do TikTok. Para mudar um valor só neste
vídeo, ponha no `config.json`, por exemplo `"safe": { "railY": 800 }` (os outros continuam os padrões).
