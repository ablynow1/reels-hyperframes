---
name: reels-hyperframes
description: Transforma um vídeo de alguém falando pra câmera (link do YouTube ou arquivo) num Reels/Shorts/TikTok vertical de ~15 segundos com edição de impacto feita com HyperFrames — escolhe o melhor trecho pela transcrição, corta e reenquadra em 9:16, recorta a pessoa do fundo e anima coisas por trás dela (balões de pergunta, símbolo e palavra gigantes, camadas de vidro 3D, moldura com painel lateral, anel de porcentagem), com legenda palavra por palavra e efeitos sonoros. Também funciona com gravação de tela narrada e narra vídeo sem fala com voz gerada pelo motor da Microsoft (a pessoa escolhe a voz). Use sempre que pedirem para "fazer um reels", "cortar um trecho", "transformar esse vídeo em short/tiktok", "editar pra postar no Instagram", "deixar a edição foda", "pegar um vídeo meu do YouTube e fazer um corte" ou mandarem um link de vídeo pedindo uma versão vertical editada — mesmo que não citem HyperFrames.
---

# Reels com HyperFrames

O resultado é um MP4 1080×1920 de ~15 s com a voz original, legenda animada palavra por palavra,
efeitos visuais passando **por trás** da pessoa e efeitos sonoros. Um exemplo real e completo está em
`assets/config.example.json` (vídeo "A Appmax é um gateway seguro?", youtube.com/watch?v=3Y6isKPyReU).

## Como a skill está organizada

- `SKILL_DIR` = a pasta desta skill (é a "Base directory" mostrada quando a skill carrega).
  Os scripts ficam em `$SKILL_DIR/scripts/` e rodam com `python3`.
- `WORK` = uma pasta de trabalho por Reels, criada no diretório atual (ex.: `./reels-appmax`):
  - `WORK/source/` → vídeo original, transcrição, quadros para olhar
  - `WORK/project/` → projeto HyperFrames (config, legendas, assets, renders)
- O `project/index.html` é **gerado** a partir de `project/config.json` por `build_composition.py`.
  Edite o config e gere de novo; não edite o HTML. O modelo (`assets/template.html`) já resolve as
  armadilhas do HyperFrames (ids de áudio, fontes, camadas, 3D, moldura) — mexer no HTML à mão
  costuma quebrar alguma delas sem aviso.
- Rode o HyperFrames sempre por `python3 "$SKILL_DIR/scripts/hf.py" "$WORK" <comando>` (check, snapshot,
  render, remove-background): usa a versão testada, desliga telemetria e checagem de atualização, não
  instala nada global e não manda quadros para IA de terceiros.

## Regras que valem sempre (e por quê)

1. **Só vídeo que a pessoa pode usar** (dela ou com permissão): o Reels vai ser publicado.
2. **Todo texto na tela sai do que a pessoa fala no trecho.** Não invente números, promessas ou nomes —
   isso vai ao ar com a cara dela. Gráfico ilustrativo (ex.: cartões "pagamento recusado" para
   "outros gateways aprovam menos") é ok quando representa a fala; avise no final que é ilustrativo.
3. **Não instale nada global** nem mude configurações do Claude Code da pessoa: nada de
   `npx hyperframes skills` / `skills update`. O `setup_project.py` instala o HyperFrames só dentro do
   projeto; o `hf.py` cuida do resto.
4. **Privacidade na tela**: em gravação de tela, corte fora barra de menu, notificações, abas e qualquer
   nome, e-mail ou agenda que apareça.
5. **Olhe os quadros antes de entregar.** O check não percebe um texto escondido atrás da cabeça nem um
   balão cobrindo o rosto; só olhando o snapshot dá para ver.
6. **Nada importante fora da área segura** (`references/safe-zone.md`). No celular o Instagram cobre o
   topo (y < 300), a base (y > 1440) e a coluna de botões (x > 860 abaixo de y 900), e em tela alta
   (iPhone 16 etc.) dá zoom e corta ~100 px de cada lado (x < 120 e x > 960). O modelo encaixa sozinho
   legendas, palavras, balões, cartões e painéis lá dentro; você confere no `celular.jpg` do review se a
   cabeça não ficou cobrindo nada que foi empurrado.
7. **Voz gerada só com o motor da Microsoft e a voz que a pessoa escolher** (`references/narration.md`):
   mande as amostras do `narrate.py` e espere a escolha. Nunca use `hyperframes tts` (Kokoro) nem o `say`
   do Mac: em português soam robóticos.
8. Fale com a pessoa em linguagem simples e mande notícias curtas nas etapas demoradas
   (transcrição, recorte, render).

## Passo a passo

### 0. Ambiente
```bash
python3 "$SKILL_DIR/scripts/check_env.py"
```
Se faltar algo, mostre à pessoa o comando de instalação que o script imprime e pare até ela instalar.

### 1. Vídeo
```bash
python3 "$SKILL_DIR/scripts/fetch_video.py" "<link ou arquivo>" "$WORK"
python3 "$SKILL_DIR/scripts/frames.py" "$WORK" overview
```
Olhe `source/frames_overview.jpg` **antes de transcrever**: tem uma pessoa falando pra câmera?
- **Sim** → siga o passo a passo abaixo.
- **Não** (gravação de tela, slides, só áudio com imagem parada) → avise a pessoa que a skill foi feita
  para quem aparece falando e pergunte se quer seguir no **modo tela** (`references/screen-recording.md`:
  sem recorte, efeitos por cima da tela) ou trocar de vídeo.
- **Sem fala, áudio ruim ou pediram narração** → narração com voz gerada
  (`references/narration.md`): roteiro, amostras de voz, a pessoa escolhe, e as legendas saem sincronizadas.
Se o yt-dlp der `HTTP Error 403`, ele está desatualizado: peça para atualizar (`brew upgrade yt-dlp`
ou `yt-dlp -U`) ou para mandar o arquivo do vídeo.

### 2. Transcrição (tempo de cada palavra)
```bash
python3 "$SKILL_DIR/scripts/transcribe.py" "$WORK" --lang pt
```
Vídeo de 10 min leva de 1 a 15 min, conforme a máquina (rode em segundo plano). Depois **leia o
`source/transcript.txt` inteiro** — é nele que você escolhe o trecho.

### 3. Escolher o trecho — a decisão que mais pesa no resultado
Se a pessoa pediu um assunto ou um tempo, siga o pedido. Se não, procure:
- **Gancho nos 2 primeiros segundos**: pergunta, afirmação forte, "todo mundo me pergunta…", número.
- **Uma ideia completa**, que faça sentido sem o resto do vídeo.
- **Algo concreto** para virar gráfico: número, comparação, contraste ("diferente de outros…", "acima de 90%").
- **13 a 16 s** (a não ser que peçam o vídeo inteiro: aí use um pedaço só, `--pieces "0-<duração>"`). Dá para tirar enrolação ("porque, primeiro…") com 1 ou 2 cortes, sempre numa pausa.
  Os pedaços entram na ordem em que você escreve — dá para trazer um gancho de depois para o começo.
- Pessoa de frente, sem texto/tela sobreposta no vídeo original e sem troca de câmera no trecho.

Ferramentas:
```bash
python3 "$SKILL_DIR/scripts/words.py" "$WORK" 440 470          # palavras com tempo + pausas
python3 "$SKILL_DIR/scripts/frames.py" "$WORK" range --from 440 --to 465   # 1 quadro/s para olhar
```
Corte dentro das pausas: comece ~0,05 s antes da primeira palavra e termine dentro da pausa depois da
última. O Whisper às vezes estica uma palavra por cima de uma pausa — confie mais na lista de pausas
(o limite de silêncio é calculado a partir do próprio áudio).

### 4. Enquadramento 9:16
```bash
python3 "$SKILL_DIR/scripts/frames.py" "$WORK" grid --at 445,452,460          # grade de 10%
python3 "$SKILL_DIR/scripts/frames.py" "$WORK" crop --at 445,452,460 --center 0.52
```
Estime o centro do rosto na grade (0 a 1 da largura) e confira no modo `crop` que o rosto ficou no meio.
Se o vídeo já for vertical, pule esta etapa. Para uma região específica (tela, zoom), use `--crop x,y,l,a`
no próximo passo.

### 5. Projeto e corte
```bash
python3 "$SKILL_DIR/scripts/setup_project.py" "$WORK"
python3 "$SKILL_DIR/scripts/make_clip.py" "$WORK" --pieces "445.05-450.88,453.52-462.55" --center 0.52
```
O `make_clip` imprime a duração e uma cor de fundo sugerida (a parede) e salva tudo em `project/clip.json`.
Se a voz tiver chiado ou ruído de ambiente, acrescente `--denoise`.

### 6. Recortar a pessoa do fundo (é a etapa mais demorada)
```bash
python3 "$SKILL_DIR/scripts/hf.py" "$WORK" remove-background assets/footage.mp4 \
  -o assets/person.webm --background-output assets/plate.webm --quality balanced
```
Leva ~0,3–0,8 s por quadro (15 s ≈ 450 quadros ≈ 3–6 min). Rode em segundo plano e siga com as
legendas e o config enquanto isso. Gera duas camadas: a pessoa (`person.webm`) e o fundo com um buraco
onde ela estava (`plate.webm`); tudo que a skill põe "por trás da pessoa" fica entre as duas.
(No modo tela, o `make_clip --screen` já cria as duas camadas; pule esta etapa.)

### 7. Legendas
```bash
python3 "$SKILL_DIR/scripts/build_captions.py" "$WORK"
```
Com narração gerada (`narrate.py`), as palavras e os tempos vêm da própria narração: não há erro de
Whisper para corrigir. Revise `project/captions.json` antes de seguir:
- **erros do Whisper** em marcas e termos técnicos (ex.: "GETAWAYS" → "GATEWAYS", "METAEDGE" → "META ADS");
- **primeira e última palavra** de cada pedaço: confira que foram ditas mesmo dentro do corte;
- **destaques**: `"y"` amarelo (marca, palavra-chave), `"g"` verde (número, resultado bom), `"r"` vermelho
  (negação, problema); `"big": true` para o bloco de impacto (uma palavra ou o número final);
- **uma linha por bloco**: acima de ~15 letras quebra em duas linhas — divida o bloco;
- **contador animado**: troque o número falado por `"#NUM"` e defina `"counter"` no config
  (ex.: valores de "12%" até "90%", terminando no número que a pessoa fala).

### 8. Roteiro dos efeitos → `project/config.json`
Leia `references/effects.md` (todos os campos, posições e tempos) e parta de `assets/config.example.json`.
Cada efeito começa na palavra que o motiva e aparece **uma vez** no vídeo. Estrutura que funcionou em 15 s:

| trecho | o que a pessoa fala | efeito |
| --- | --- | --- |
| 0–3 s | gancho / o que perguntam para ela | `bubbles` (balões de pergunta; `"front": true` num close) |
| 3–5 s | a pergunta em si | `bigSymbol` ("?", "!", "$") |
| marca ou palavra-chave | "…indico a APPMAX" | `bigWord` (`"front": true` num close) + soco de câmera (`camera.punches`) |
| explicação | "alta taxa de aprovação…" | `glass` (camadas de vidro com cartão) |
| comparação ou lista | "diferente de outros gateways…" | `frame` (moldura + manchete + cartões) |
| número final | "acima de 90%" | `ring` + contador na legenda + soco de câmera |

Para algo técnico que precisa ser explicado (peça, processo, comparação), use `diagram` (ilustração SVG
que você desenha, montada por etapas); para ranking ou lista com posições, `table`. Vídeo longo (30–60 s)
pede efeitos espalhados a cada 5–8 s; `bigWord` e `bigSymbol` podem repetir (lista), com `"front": true`
quando a cabeça ocupa o topo da tela.

Use só os efeitos que a fala sustenta — 4 a 6 em 15 s já é muito. `glass` e `frame` mexem na cena
inteira e não podem se sobrepor; socos de câmera com pelo menos 1 s de distância. Fundo claro pede
cores escuras nos textos gigantes (veja "Fundo claro" em `effects.md`). O `"sfx": "auto"` monta o som
sozinho a partir dos efeitos.

### 9. Gerar e conferir
```bash
python3 "$SKILL_DIR/scripts/build_composition.py" "$WORK"
python3 "$SKILL_DIR/scripts/hf.py" "$WORK" check
```
Resolva os AVISOS do builder e os erros do check até sair `Check passed`. A lista "ÁREA SEGURA" do
builder só informa o que o modelo vai empurrar para dentro (não precisa mexer, mas confira no passo 10);
um erro `[área segura] … encurte o texto` no check pede texto menor. Pode ignorar:
`composition_file_too_large` (o arquivo tem todos os efeitos) e contraste baixo das **legendas** em fundo
claro (elas têm contorno preto, que o check não enxerga).

### 10. Olhar os quadros e ajustar posições
```bash
python3 "$SKILL_DIR/scripts/review.py" "$WORK"
```
O `review.py` lê o config e tira quadros sozinho em cada entrada e saída de efeito, nos socos de câmera e
no fim (ideia do pdoom-video: revisar toda troca de cena). Abra as duas folhas:
- `project/snaps_review/contact-sheet.jpg`: balão ou texto sumido atrás da cabeça, coisa cobrindo o
  rosto, legenda em duas linhas, cartão cortado;
- `project/snaps_review/celular.jpg`: os mesmos quadros com a área segura — **faixa vermelha** é onde o
  Instagram cobre ou o celular corta, **linha amarela** é o topo das legendas. Nenhum texto, número ou
  cartão pode encostar no vermelho (se encostar, algo foi feito à mão fora do modelo).

Para olhar um tempo específico:
`python3 "$SKILL_DIR/scripts/hf.py" "$WORK" snapshot --at 7.2 --no-end -o snaps`. Num close, a cabeça ocupa mais ou
menos x 270–900 e y 150–1120 da tela 1080×1920; o que passa por trás tem que ficar na lateral e dentro da
área segura, o que num close quase não sobra — palavra gigante e balões vão melhor com `"front": true`.
Ajuste o config, gere de novo e tire outro snapshot até ficar limpo.

### 11. Render
```bash
python3 "$SKILL_DIR/scripts/hf.py" "$WORK" render -f 30 -q high -w 2 -o renders/reel.mp4
```
Leva de 30 s a 3 min. Com pouca memória, use `-w 1`. Em gravação de tela, acrescente
`--video-frame-format png` (texto de interface mais nítido).

**Acabamento (opcional, recomendado quando há socos de câmera e giros):** borrão de movimento e grão de
filme, inspirados no pdoom-video. Renderiza a 60 fps (o dobro do tempo) e mistura para 30:
```bash
python3 "$SKILL_DIR/scripts/hf.py" "$WORK" render -f 60 -q high -w 2 -o renders/reel60.mp4
python3 "$SKILL_DIR/scripts/finish.py" "$WORK" --blur --grain 5
```
O arquivo final passa a ser `renders/reel_final.mp4`. O grão (4 a 8) também disfarça imagem suavizada
de vídeo 720p.

### 12. Revisão final
```bash
python3 "$SKILL_DIR/scripts/sheet.py" "$WORK/project/renders/reel.mp4" --fps 2 --celular
python3 "$SKILL_DIR/scripts/review.py" "$WORK" --render
```
Olhe a folha inteira (2 quadros/s, com a área segura marcada) e as folhas das trocas de efeito do vídeo
pronto (`renders/revisao_trocas.jpg` e `renders/revisao_celular.jpg`). Para uma transição em câmera lenta:
`sheet.py … --from 5.6 --to 6.4 --fps 10`. Se algo escapou, volte ao 10.

### 13. Entrega
Diga onde está o arquivo (copie para `~/Downloads` se pedirem), qual trecho usou (tempo + a frase),
quais efeitos entraram e as ressalvas: gráficos ilustrativos e, se o vídeo de origem for 720p,
que a imagem fica um pouco mais suave que uma gravação vertical nativa.

## Referências
- `references/effects.md` — cada efeito: campos, valores padrão, posição e tempo.
- `references/safe-zone.md` — área segura do Reels: os números, o que o modelo encaixa sozinho e o que conferir.
- `references/screen-recording.md` — modo tela (vídeo sem pessoa aparecendo).
- `references/narration.md` — narração com voz gerada (motor da Microsoft; a pessoa escolhe a voz).
- `references/troubleshooting.md` — erros conhecidos e como resolver.
- `assets/config.example.json` — config real completo do Reels de exemplo.
