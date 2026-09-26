---
name: reels-hyperframes
description: Transforma um vídeo de alguém falando pra câmera (link do YouTube ou arquivo) num Reels/Shorts/TikTok vertical de ~15 segundos com edição de impacto feita com HyperFrames — escolhe o melhor trecho pela transcrição, corta e reenquadra em 9:16, recorta a pessoa do fundo e anima coisas por trás dela (balões de pergunta, símbolo e palavra gigantes, camadas de vidro 3D, moldura com painel lateral, anel de porcentagem), com legenda palavra por palavra e efeitos sonoros. Use sempre que pedirem para "fazer um reels", "cortar um trecho", "transformar esse vídeo em short/tiktok", "editar pra postar no Instagram", "deixar a edição foda", "pegar um vídeo meu do YouTube e fazer um corte" ou mandarem um link de vídeo pedindo uma versão vertical editada — mesmo que não citem HyperFrames.
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

## Regras que valem sempre (e por quê)

1. **Só vídeo que a pessoa pode usar** (dela ou com permissão): o Reels vai ser publicado.
2. **Todo texto na tela sai do que a pessoa fala no trecho.** Não invente números, promessas ou nomes —
   isso vai ao ar com a cara dela. Gráfico ilustrativo (ex.: cartões "pagamento recusado" para
   "outros gateways aprovam menos") é ok quando representa a fala; avise no final que é ilustrativo.
3. **Não instale nada global.** Nada de `npx hyperframes skills` / `skills update` (instalaria skills no
   Claude Code da pessoa) nem mudança de configuração dela. O `setup_project.py` já instala o
   HyperFrames só dentro do projeto e desliga a telemetria.
4. **Olhe os quadros antes de entregar.** O `hyperframes check` não percebe um texto escondido atrás da
   cabeça nem um balão cobrindo o rosto; só olhando o snapshot dá para ver.
5. Fale com a pessoa em linguagem simples e mande notícias curtas nas etapas demoradas
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
```
Se o yt-dlp der `HTTP Error 403`, ele está desatualizado: peça para atualizar (`brew upgrade yt-dlp`
ou `yt-dlp -U`) ou para mandar o arquivo do vídeo.

### 2. Transcrição (tempo de cada palavra)
```bash
python3 "$SKILL_DIR/scripts/transcribe.py" "$WORK" --lang pt
```
Vídeo de 10 min leva de 1 a 10 min, conforme a máquina (rode em segundo plano se der). Depois **leia o
`source/transcript.txt` inteiro** — é nele que você escolhe o trecho.

### 3. Escolher o trecho — a decisão que mais pesa no resultado
Se a pessoa pediu um assunto ou um tempo, siga o pedido. Se não, procure:
- **Gancho nos 2 primeiros segundos**: pergunta, afirmação forte, "todo mundo me pergunta…", número.
- **Uma ideia completa**, que faça sentido sem o resto do vídeo.
- **Algo concreto** para virar gráfico: número, comparação, contraste ("diferente de outros…", "acima de 90%").
- **13 a 16 s.** Dá para tirar enrolação ("porque, primeiro…") com 1 ou 2 cortes, sempre numa pausa.
- Pessoa de frente, sem texto/tela sobreposta no vídeo original e sem troca de câmera no trecho.

Ferramentas:
```bash
python3 "$SKILL_DIR/scripts/words.py" "$WORK" 440 470          # palavras com tempo + pausas
python3 "$SKILL_DIR/scripts/frames.py" "$WORK" range --from 440 --to 465   # 1 quadro/s para olhar
```
Corte dentro das pausas: comece ~0,05 s antes da primeira palavra e termine dentro da pausa depois da
última. O Whisper às vezes estica uma palavra por cima de uma pausa — confie mais na lista de pausas.

### 4. Enquadramento 9:16
```bash
python3 "$SKILL_DIR/scripts/frames.py" "$WORK" grid --at 445,452,460          # grade de 10%
python3 "$SKILL_DIR/scripts/frames.py" "$WORK" crop --at 445,452,460 --center 0.52
```
Estime o centro do rosto na grade (0 a 1 da largura) e confira no modo `crop` que o rosto ficou no meio.
Se o vídeo já for vertical, pule esta etapa.

### 5. Projeto e corte
```bash
python3 "$SKILL_DIR/scripts/setup_project.py" "$WORK"
python3 "$SKILL_DIR/scripts/make_clip.py" "$WORK" --pieces "445.05-450.88,453.52-462.55" --center 0.52
```
O `make_clip` imprime a duração e uma cor de fundo sugerida (a parede) e salva tudo em `project/clip.json`.

### 6. Recortar a pessoa do fundo (é a etapa mais demorada)
```bash
cd "$WORK/project" && npx -y hyperframes@0.8.78 remove-background assets/footage.mp4 \
  -o assets/person.webm --background-output assets/plate.webm --quality balanced
```
Leva ~0,3–0,8 s por quadro (15 s ≈ 450 quadros ≈ 3–6 min). Rode em segundo plano e siga com as
legendas e o config enquanto isso. Gera duas camadas: a pessoa (`person.webm`) e o fundo com um buraco
onde ela estava (`plate.webm`); tudo que a skill põe "por trás da pessoa" fica entre as duas.

### 7. Legendas
```bash
python3 "$SKILL_DIR/scripts/build_captions.py" "$WORK"
```
Revise `project/captions.json` antes de seguir:
- **erros do Whisper** em marcas e termos técnicos (ex.: "GETAWAYS" → "GATEWAYS");
- **destaques**: `"y"` amarelo (marca, palavra-chave), `"g"` verde (número, resultado bom), `"r"` vermelho
  (negação, problema); `"big": true` para o bloco de impacto (uma palavra ou o número final);
- **uma linha por bloco**: acima de ~15 letras quebra em duas linhas — divida o bloco;
- **contador animado**: troque o número falado por `"#NUM"` e defina `"counter"` no config
  (ex.: valores de "12%" até "90%", terminando no número que a pessoa fala).

### 8. Roteiro dos efeitos → `project/config.json`
Leia `references/effects.md` (todos os campos, posições e tempos) e parta de `assets/config.example.json`.
Cada efeito começa na palavra que o motiva. Estrutura que funcionou em 15 s:

| trecho | o que a pessoa fala | efeito |
| --- | --- | --- |
| 0–3 s | gancho / o que perguntam para ela | `bubbles` (balões de pergunta por trás) |
| 3–5 s | a pergunta em si | `bigSymbol` ("?", "!", "$") |
| marca ou palavra-chave | "…indico a APPMAX" | `bigWord` + soco de câmera (`camera.punches`) |
| explicação | "alta taxa de aprovação…" | `glass` (camadas de vidro com cartão) |
| comparação ou lista | "diferente de outros gateways…" | `frame` (moldura + manchete + cartões) |
| número final | "acima de 90%" | `ring` + contador na legenda + soco de câmera |

Use só os efeitos que a fala sustenta — 4 a 6 em 15 s já é muito. `glass` e `frame` mexem na cena
inteira e não podem se sobrepor; socos de câmera com pelo menos 1 s de distância. O `"sfx": "auto"`
monta o som sozinho a partir dos efeitos.

### 9. Gerar e conferir
```bash
python3 "$SKILL_DIR/scripts/build_composition.py" "$WORK"
cd "$WORK/project" && npx -y hyperframes@0.8.78 check
```
Resolva os AVISOS do builder e os erros do check até sair `Check passed`. O único aviso esperado é
`composition_file_too_large` (o arquivo é grande porque tem todos os efeitos; pode ignorar).

### 10. Olhar os quadros e ajustar posições
```bash
cd "$WORK/project" && npx -y hyperframes@0.8.78 snapshot --at 1.9,3.6,5.4,7,10,13.5 --no-end -o snaps
```
Abra `snaps/contact-sheet.jpg` (um tempo por efeito) e procure: balão ou texto sumido atrás da cabeça,
coisa cobrindo o rosto, legenda em duas linhas, cartão cortado. Num close, a cabeça ocupa mais ou menos
x 270–900 e y 150–1120 da tela 1080×1920; o que passa por trás tem que ficar nas laterais ou acima da
cabeça. Ajuste o config, gere de novo e tire outro snapshot até ficar limpo.

### 11. Render
```bash
cd "$WORK/project" && npx -y hyperframes@0.8.78 render -f 30 -q high -w 2 -o renders/reel.mp4
```
Leva de 1 a 3 min. Com pouca memória, use `-w 1`.

### 12. Revisão final
```bash
python3 "$SKILL_DIR/scripts/sheet.py" "$WORK/project/renders/reel.mp4" --fps 2
python3 "$SKILL_DIR/scripts/sheet.py" "$WORK/project/renders/reel.mp4" --from 5.6 --to 6.4 --fps 10
```
Olhe a folha inteira e as transições (entrada e saída do vidro e da moldura). Se algo escapou, volte ao 10.

### 13. Entrega
Diga onde está o arquivo (copie para `~/Downloads` se pedirem), qual trecho usou (tempo + a frase),
quais efeitos entraram e as ressalvas: gráficos ilustrativos e, se o vídeo de origem for 720p,
que a imagem fica um pouco mais suave que uma gravação vertical nativa.

## Referências
- `references/effects.md` — cada efeito: campos, valores padrão, posição e tempo.
- `references/troubleshooting.md` — erros conhecidos e como resolver.
- `assets/config.example.json` — config real completo do Reels de exemplo.
