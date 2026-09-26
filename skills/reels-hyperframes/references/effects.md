# Efeitos e campos do `config.json`

Tudo em segundos (tempo do corte, começando em 0) e em pixels da tela vertical **1080×1920**.
Qualquer efeito pode ser omitido. Exemplo completo: `assets/config.example.json`.

## Sumário
- Campos gerais
- Câmera (`camera`)
- Balões por trás (`effects.bubbles`)
- Símbolo gigante (`effects.bigSymbol`)
- Palavra gigante (`effects.bigWord`)
- Camadas de vidro 3D (`effects.glass`)
- Moldura + painel (`effects.frame`)
- Anel de porcentagem (`effects.ring`)
- Legendas e contador
- Efeitos sonoros
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

## Câmera
```json
"camera": { "punches": [5.31, 13.07], "push": true, "punchHold": 0.5 }
```
- Sempre tem entrada com zoom + desfoque + flash em 0 s.
- `push`: aproximação lenta até o primeiro soco (padrão ligado).
- `punches`: socos de câmera (zoom rápido + tremida + flash) — ponha na palavra de impacto
  (marca, número). Mínimo 1 s entre eles. `punchHold` = quanto tempo o zoom segura antes de voltar.

## Balões por trás
Para "todo mundo me pergunta…", "meus clientes falam…": as perguntas surgem por trás da pessoa.
```json
"bubbles": {
  "out": 2.62,
  "items": [
    { "text": "qual plataforma você usa?", "at": 0.3, "left": 24, "top": 470, "width": 330, "rot": -3, "tail": "r" },
    { "text": "qual você indica?", "at": 0.95, "left": 44, "top": 190, "width": 270, "rot": 2, "tail": "r" },
    { "text": "é confiável?", "at": 1.6, "left": 34, "top": 900, "width": 300, "rot": -2, "tail": "r" }
  ]
}
```
- `at` = quando cada balão aparece (espalhe ~0,6 s); `out` = quando todos saem.
- Texto curto (2 linhas no máximo, `width` 270–340). `tail` "r" ou "l" = lado do bico.
- Posição: nas laterais, encostando no rosto só com a pontinha (é isso que dá a sensação de "por trás").
  Num close quase não sobra espaço à direita; empilhar os três à esquerda funciona bem.
- As perguntas precisam ser coerentes com a fala (paráfrases do que ela diz que perguntam).

## Símbolo gigante
```json
"bigSymbol": { "text": "?", "in": 2.72, "out": 4.6, "left": 10, "top": 110, "size": 980, "color": "#6a2ee8" }
```
- Gira em 3D ao entrar. Um caractere ("?", "!", "$", "%", "×").
- Fica de lado da cabeça (`left` 10 ou ~800) — no meio ele some atrás da pessoa.
- `color` com contraste contra a parede (roxo/escuro em parede clara; amarelo em parede escura).

## Palavra gigante
```json
"bigWord": { "text": "APPMAX", "at": 5.31, "out": 5.95, "top": -10, "size": 300, "color": "#ffffff", "glow": "rgba(123, 63, 242, 0.9)" }
```
- Bate por trás da cabeça na hora da palavra. Combine com um soco de câmera no mesmo `at`.
- Fica **acima** da cabeça (`top` −10 a 60): o cabelo cobre só a parte de baixo das letras do meio.
- Até ~7 letras em `size` 300; palavras maiores, diminua o `size`.

## Camadas de vidro 3D
A cena gira e se separa em três placas de vidro: fundo, cartão, pessoa. Depois junta de novo.
```json
"glass": {
  "in": 5.83, "out": 8.25, "angle": 24,
  "cardIn": 6.2, "title": "TAXA DE", "accent": "APROVAÇÃO", "icon": "card",
  "sub": "CARTÃO DE CRÉDITO", "subAt": 7.91,
  "left": 30, "top": 540, "width": 420
}
```
- Bom para a frase que explica o ponto principal. Dura de 2 a 3 s.
- `in` numa emenda de corte esconde o pulo da imagem.
- Cartão: `title` (branco) + `accent` (verde) + `icon` (`"card"` cartão de crédito, `"check"` ✓, ou omita)
  + `sub` (amarelo, aparece em `subAt`). Sem `title`/`accent`, só as camadas giram.
- Posição do cartão: lado esquerdo (`left` ~30, `width` ≤ 420). Com `angle` positivo a pessoa se desloca
  para a direita e revela o lado esquerdo da camada do meio.

## Moldura + painel lateral
A pessoa encolhe para uma moldura à direita; manchete em cima e cartões à esquerda.
```json
"frame": {
  "in": 8.62, "out": 12.92, "x": 440, "y": 420, "w": 540,
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
- A moldura padrão (x 440, y 420, largura 540) deixa a coluna da esquerda (x 50–410) para os cartões.
- Se vier depois do `glass`, comece pelo menos 0,37 s depois do `glass.out` (o builder avisa).

## Anel de porcentagem
```json
"ring": { "in": 13.05, "drawAt": 13.1, "drawDur": 1.15, "percent": 90, "cx": 540, "cy": 620, "r": 430, "color": "#29e07a" }
```
- Um anel verde enche até `percent` por trás da cabeça. Centralize no rosto (`cx`, `cy`): num close
  típico, (540, 620) com raio 430.
- Combine com o contador na legenda e um soco de câmera no mesmo tempo.

## Legendas e contador
Cada bloco: `{ "s": início, "e": fim, "big": true?, "w": [[PALAVRA, tempo, estilo?], ...] }`.
- Estilos: `"y"` amarelo, `"g"` verde, `"r"` vermelho. `big` = fonte maior (bloco de impacto).
- Um bloco por vez, uma linha (até ~15 letras; `big` até ~12).
- Contador: a palavra `"#NUM"` mostra `counter.values` um depois do outro a cada `counter.step`
  segundos, a partir do tempo da palavra.
- As legendas ficam em y ≈ 1250–1340 (terço de baixo, acima da interface do Instagram).

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

## Zonas da tela (1080×1920)
- **Cabeça num close**: x ≈ 270–900, y ≈ 150–1120. O que passa por trás tem que ficar fora disso
  (laterais ou acima), senão some.
- **Legendas**: y ≈ 1250–1340.
- **Interface do Instagram**: evite texto em y > 1570 (legenda do post, botões) e na faixa direita
  x > 960 entre y 1000 e 1650 (curtir, comentar, compartilhar). O topo (y < 150) tem pouca interface.
