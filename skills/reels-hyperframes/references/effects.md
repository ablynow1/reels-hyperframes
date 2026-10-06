# Efeitos e campos do `config.json`

Tudo em segundos (tempo do corte, começando em 0) e em pixels da tela vertical **1080×1920**.
Qualquer efeito pode ser omitido. `bigWord`, `bigSymbol`, `diagram` e `table` aceitam uma **lista** (aparecem
quantas vezes quiser); `bubbles`, `glass`, `frame` e `ring` aparecem uma vez. Exemplo completo:
`assets/config.example.json`.

**Área segura** (`references/safe-zone.md`): texto fica em x 120–960 (só até 860 abaixo de y 900) e
y 300–1150; as legendas em y 1170–1290. O modelo encaixa sozinho tudo que sair disso (empurra para
dentro e, se precisar, diminui a fonte), contando o zoom da câmera. As posições abaixo já respeitam a
área; o que você precisa conferir é se a **cabeça** não está cobrindo algo que passa por trás.

## Sumário
- Campos gerais
- Câmera (`camera`)
- Balões por trás (`effects.bubbles`)
- Símbolo gigante (`effects.bigSymbol`)
- Palavra gigante (`effects.bigWord`)
- Camadas de vidro 3D (`effects.glass`)
- Moldura + painel (`effects.frame`)
- Anel de porcentagem (`effects.ring`)
- Ilustração explicativa (`effects.diagram`)
- Tabela / ranking (`effects.table`)
- Legendas e contador
- Efeitos sonoros
- Fundo claro
- Zonas da tela (onde pôr cada coisa)

## Campos gerais

```json
{
  "duration": 14.86,
  "fill": "#e3d2c5",
  "camera": { "punches": [5.31, 13.07] },
  "counter": { "values": ["12%", "27%", "43%", "58%", "71%", "82%", "88%", "90%"], "step": 0.09 },
  "effects": { },
  "sfx": "auto",
  "captions": "captions.json"
}
```
- `duration` e `fill` vêm do `clip.json` se você não puser. `fill` é a cor que aparece no lugar da
  pessoa quando o fundo aparece sozinho (nas camadas de vidro vira uma "silhueta"); use a cor da parede.
- `captions`: lista de blocos ou o nome do arquivo (`captions.json`, padrão).
- `safe` (opcional): muda um valor da área segura só neste vídeo, ex.: `"safe": { "railY": 800 }`.

## Câmera
```json
"camera": { "punches": [5.31, 13.07], "push": true, "punchHold": 0.5 }
```
- Sempre tem entrada com zoom + desfoque + flash em 0 s.
- `push`: aproximação lenta até o primeiro soco (padrão ligado).
- `punches`: socos de câmera (zoom rápido + tremida + flash) — ponha na palavra de impacto
  (marca, número). Mínimo 1 s entre eles. `punchHold` = quanto tempo o zoom segura antes de voltar.

## Balões por trás
Para "todo mundo me pergunta…", "meus clientes falam…": as perguntas surgem em volta da pessoa (por trás
ou, num close, na frente).
```json
"bubbles": {
  "front": true,
  "out": 2.62,
  "items": [
    { "text": "qual plataforma você usa?", "at": 0.3, "left": 150, "top": 340, "width": 320, "rot": -3, "tail": "r" },
    { "text": "qual você indica?", "at": 0.95, "left": 560, "top": 410, "width": 280, "rot": 2, "tail": "l" },
    { "text": "é confiável?", "at": 1.6, "left": 150, "top": 860, "width": 250, "rot": -2, "tail": "r" }
  ]
}
```
- `at` = quando cada balão aparece (espalhe ~0,6 s); `out` = quando todos saem.
- Texto curto (2 linhas no máximo, `width` 240–320). `tail` "r" ou "l" = lado do bico.
- **Por trás** (padrão): na lateral, a partir de x 120 e y 300, encostando no rosto só com a pontinha —
  funciona quando sobra parede ao lado da cabeça (plano mais aberto).
- **Na frente** (`"front": true`): o certo num close, em que o rosto ocupa quase toda a área segura. Ponha
  os balões sobre o cabelo/testa (y 300–550) e nas bochechas, **nunca sobre olhos e boca** (o exemplo
  acima é de um close).
- As perguntas precisam ser coerentes com a fala (paráfrases do que ela diz que perguntam).

## Símbolo gigante
```json
"bigSymbol": { "text": "?", "in": 2.72, "out": 4.6, "left": 180, "top": 335, "size": 560, "color": "#6a2ee8" }
```
- Gira em 3D ao entrar. Um caractere ("?", "!", "$", "%", "×").
- Fica de lado da cabeça, na parede que sobra entre a margem (x 120) e o rosto — no meio ele some atrás
  da pessoa. Num close o espaço é estreito: `size` ~500–600; em plano aberto, até ~900 (o modelo encolhe o
  que passar da área segura, já contando o giro).
- `color` com contraste contra a parede (roxo/escuro em parede clara; amarelo em parede escura).

## Palavra gigante
```json
"bigWord": { "text": "APPMAX", "at": 5.31, "out": 5.95, "front": true, "size": 240 }
```
- Bate na hora da palavra. Combine com um soco de câmera no mesmo `at` (o encaixe já conta o zoom do soco).
- **Na frente** (`"front": true`, contorno preto, amarelo por padrão, `size` padrão 240): sem `top`, fica
  logo acima das legendas. É o certo num **close** — selfie, vídeo no carro, cabeça no alto da tela —,
  porque o topo da tela agora é área da interface do Instagram e não sobra lugar acima da cabeça.
- **Por trás** (sem `front`, branca com brilho roxo, `size` padrão 300): sem `top`, fica no alto da área
  segura (y ≈ 300). Só funciona quando a cabeça começa bem abaixo disso (plano mais aberto); senão a
  cabeça cobre as letras — confira no `celular.jpg`.
- Para várias palavras, use uma lista: `"bigWord": [ {...}, {...} ]`.
- Até ~7 letras em `size` 300 (palavras maiores o modelo diminui sozinho até caber em x 120–960).

## Camadas de vidro 3D
A cena gira e se separa em três placas de vidro: fundo, cartão, pessoa. Depois junta de novo.
```json
"glass": {
  "in": 5.83, "out": 8.25, "angle": 24,
  "cardIn": 6.2, "title": "TAXA DE", "accent": "APROVAÇÃO", "icon": "card",
  "sub": "CARTÃO DE CRÉDITO", "subAt": 7.91,
  "left": 40, "top": 540, "width": 300
}
```
- Bom para a frase que explica o ponto principal. Dura de 2 a 3 s.
- `in` numa emenda de corte esconde o pulo da imagem.
- Cartão: `title` (branco) + `accent` (verde) + `icon` (`"card"` cartão de crédito, `"check"` ✓, ou omita)
  + `sub` (amarelo, aparece em `subAt`). Sem `title`/`accent`, só as camadas giram.
- Posição do cartão: lado esquerdo (`left` ~40, `width` ≤ 300). No giro a cena encolhe para o centro, então
  na tela o cartão aparece bem mais para dentro (left 40 vira x ≈ 150); o modelo mede a caixa real durante o
  giro e só empurra se sair da área segura. Com `angle` positivo a pessoa se desloca para a direita e revela
  o lado esquerdo da camada do meio — mas no fim do giro ela volta um pouco: cartão largo demais fica com a
  ponta atrás da cabeça.

## Moldura + painel lateral
A pessoa encolhe para uma moldura à direita; manchete em cima e cartões à esquerda.
```json
"frame": {
  "in": 8.62, "out": 12.92,
  "headline": "OUTROS GATEWAYS",
  "cards": [
    { "t1": "Pagamento", "t2": "RECUSADO", "kind": "bad", "at": 9.09 },
    { "t1": "Pagamento", "t2": "RECUSADO", "kind": "bad", "at": 9.45 },
    { "t1": "Pagamento", "t2": "RECUSADO", "kind": "bad", "at": 9.83 }
  ],
  "alertAt": 11.67, "panelOut": 12.62
}
```
- Bom para comparação ("diferente de outros…") ou lista (3 itens).
- `kind`: `"bad"` (✕ vermelho) ou `"good"` (✓ verde). `t1` pequeno em cima, `t2` grande embaixo (até ~10 letras).
- `alertAt`: os cartões tremem e a manchete fica vermelha (use no "não", "nunca").
- Sem `x`/`y`/`w`, o modelo faz o layout dentro da área segura: manchete em y 300 (fonte de até 150,
  ajustada à largura), moldura de largura 500 encostada em x 960, logo abaixo da manchete, e os cartões
  entre x 120 e a moldura (encolhem juntos se não couberem). Só ponha `x`, `y`, `w`, `headlineTop`,
  `headlineSize`, `panelX`, `panelY`, `panelW` se precisar — valores fora da área são corrigidos.
- Se vier depois do `glass`, comece pelo menos 0,37 s depois do `glass.out` (o builder avisa).

## Anel de porcentagem
```json
"ring": { "in": 13.05, "drawAt": 13.1, "drawDur": 1.15, "percent": 90, "cx": 540, "cy": 675, "r": 340, "color": "#29e07a" }
```
- Um anel verde enche até `percent` por trás da cabeça. Centralize no rosto (`cx`, `cy`): num close
  típico, (540, 675) com raio 340. O modelo encolhe/desce o anel para ele caber inteiro na área segura
  (topo em y 300, laterais em 120 e 960), já contando o zoom do soco de câmera.
- Combine com o contador na legenda e um soco de câmera no mesmo tempo.

## Ilustração explicativa
Um painel escuro sobe por cima do vídeo (o fundo escurece) com um SVG que vai se montando por etapas — bom
para explicar algo técnico que a pessoa fala (motor, processo, antes × depois).
```json
"diagram": {
  "in": 33.3, "out": 41.6, "svg": "engine.svg",
  "title": "POR QUE O 6.7 É", "accent": "MAIS BAIXO", "subtitle": "ilustração · fora de escala",
  "steps": [33.55, 35.26, 35.9, 37.54, 39.79]
}
```
- `svg`: arquivo em `project/assets/` (o builder embute no HTML). Marque as partes com `data-step="1"`,
  `data-step="2"`… — cada uma aparece no tempo correspondente de `steps` (a etapa 1 sem tempo entra logo).
- Desenhe o SVG você mesmo (formas simples, texto em "Bebas Neue"/"Montserrat"), com `viewBox` justo.
  O painel tem ~770 px de área útil (~670 px se for mais alto que y 900, para não entrar embaixo dos
  botões): desenhe com `viewBox` de ~700 de largura, texto com 26 px ou mais e nada importante nos cantos.
  Ilustração sem medida real? Escreva "ilustração · fora de escala".
- O painel começa em y 300 (`top` só para descer mais) e termina acima das legendas; se não couber, encolhe.
- `dim` (0–1) = quanto o vídeo escurece por trás (padrão 0,78). `out` no fim do vídeo = fica até o final.

## Tabela / ranking
Lista com posições que vão entrando uma a uma (de baixo para cima com `"order": "up"`), destaque dourado.
```json
"table": {
  "in": 50.18, "out": 60.15,
  "title": "QUEM ELE", "accent": "DESBANCOU", "subtitle": "ranking de aceleração lateral",
  "order": "up", "rowStart": 50.7, "rowStep": 0.45, "flashAt": 57.24,
  "rows": [
    { "label": "Corvette Grand Sport Z52", "value": "1,23 G", "hl": "gold" },
    { "label": "McLaren 765LT Spider" },
    { "label": "Corvette C8 ZR1", "hl": "mark" }
  ]
}
```
- `hl`: `"gold"` (linha campeã) ou `"mark"` (borda vermelha, para chamar atenção). `value` é opcional —
  só ponha número que a pessoa falou ou que veio de uma fonte confirmada.
- Até 10 linhas cabem entre y 300 e 1150 (acima das legendas; com 10 linhas o painel encolhe um pouco).
  Nome da linha com até ~26 letras. `rowTimes` permite tempos manuais.
- `flashAt` faz a linha dourada pulsar (combine com um soco de câmera).

## Legendas e contador
Cada bloco: `{ "s": início, "e": fim, "big": true?, "w": [[PALAVRA, tempo, estilo?], ...] }`.
- Estilos: `"y"` amarelo, `"g"` verde, `"r"` vermelho. `big` = fonte maior (bloco de impacto).
- Um bloco por vez, uma linha (até ~15 letras; `big` até ~12). Bloco mais largo que x 120–860 sai com
  fonte menor (o modelo ajusta) — melhor dividir.
- Contador: a palavra `"#NUM"` mostra `counter.values` um depois do outro a cada `counter.step`
  segundos, a partir do tempo da palavra. Valores longos ("1,23G") pedem `counter.width` maior (em em, padrão 3,1).
- As legendas ficam em y ≈ 1170–1290, centralizadas; um bloco largo desliza um pouco para a esquerda para
  não passar embaixo da coluna de botões (x > 860).

## Efeitos sonoros
`"sfx": "auto"` (padrão) monta: whoosh na entrada, pop em cada balão e cartão, whoosh no símbolo e nas
camadas, impacto em cada soco, riser terminando no último soco, brilho no fim do anel.
Lista manual, se quiser controlar:
```json
"sfx": [ { "file": "whoosh.mp3", "at": 0, "vol": 0.3 }, { "file": "impact-bass-1.mp3", "at": 5.31, "vol": 0.42 } ]
```
Arquivos disponíveis (vêm no pacote do HyperFrames): whoosh, whoosh-short, whoosh-cinematic, pop,
impact-bass-1, impact-bass-2, sparkle, riser, chime, ping, click, click-soft, notification, glitch-1/2/3,
error, typing, key-press (`.mp3`). Volume ~0,3: o som fica por baixo da voz.

## Fundo claro
As cores padrão (texto gigante branco com brilho roxo, símbolo roxo) somem em parede branca ou tela clara.
Em fundo claro:
- `bigWord`: `"color": "#111111"` e um `glow` colorido (ex.: `"rgba(255, 196, 0, 0.9)"`);
- `bigSymbol`: cor escura ou bem saturada (ex.: `"#111111"`, `"#6a2ee8"`);
- `ring`: cor forte (ex.: `"#1faa59"`) e `glow` mais fraco.
As legendas já têm contorno preto; o aviso de contraste delas no check pode ser ignorado.

## Zonas da tela (1080×1920)
- **Área segura** (detalhes em `references/safe-zone.md`): fora dela a interface cobre ou o celular corta.
  - topo y < 300: status, Dynamic Island e cabeçalho do Reels;
  - base y > 1440: @ do perfil, legenda do post, música;
  - laterais x < 120 e x > 960: corte do zoom em celular alto (iPhone 16 perde ~100 px de cada lado);
  - coluna de botões x > 860 com y > 900: curtir, comentar, compartilhar.
- **Legendas**: y ≈ 1170–1290; os outros textos ficam acima de 1150.
- **Cabeça num close**: x ≈ 270–900, y ≈ 150–1120. O que passa por trás tem que ficar fora disso
  (na lateral) **e** dentro da área segura — num close isso quase não existe: prefira `"front": true`.
