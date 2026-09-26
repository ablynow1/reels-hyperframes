# Problemas conhecidos e soluções

## Download
- **`HTTP Error 403` no yt-dlp** → yt-dlp desatualizado. `brew upgrade yt-dlp` (Mac) ou `yt-dlp -U`.
  Se continuar, peça o arquivo do vídeo à pessoa (ela é a dona).
- **Vídeo sem áudio** → a skill precisa da fala; peça outra fonte.

## Transcrição
- **Nenhum motor disponível** → Mac com chip Apple: `pip3 install mlx-whisper`; outros: `pip3 install faster-whisper`;
  ou `brew install whisper-cpp` (o `transcribe.py` usa o que existir).
- **Texto saiu em inglês** → modelo `.en` traduz. Use sempre `--lang` com o idioma da fala.
- **Palavra com tempo esticado** (ex.: "qual" durando 1,2 s) → o Whisper colou uma pausa na palavra.
  Use as pausas do `words.py` para cortar; o `build_captions.py` já corrige palavras longas demais.
- **Demora muito** → outras coisas pesadas rodando na máquina disputam a CPU. Espere, ou transcreva só um
  trecho: extraia com `ffmpeg -ss INICIO -t DURACAO` e ajuste os tempos.

## Check do HyperFrames
- **`media_missing_id`** → `<audio>` sem `id` sai MUDO no render. O builder já põe ids; não escreva áudio à mão.
- **`Font families used without @font-face declaration`** → fonte fora da lista automática (ex.: Anton, Impact).
  Use Montserrat, Bebas Neue, League Gothic, Oswald, Archivo Black, Poppins ou Inter.
- **`content_overlap` entre balões** → dois balões no mesmo lugar; mude `left`/`top`.
- **Contraste baixo** (símbolo claro em parede clara) → troque `color` do `bigSymbol`.
- **`composition_file_too_large`** → aviso esperado; pode ignorar.
- **`canvas_overflow` informativo** em texto gigante → normal quando o texto encosta na borda durante o zoom.

## Visual
- **Balão/palavra sumiu** → está atrás da cabeça. Veja "Zonas da tela" em `effects.md` e mova para o lado ou para cima.
- **Legenda em 2 linhas** → bloco longo demais; divida em dois no `captions.json`.
- **Silhueta clara nas camadas de vidro** → é o buraco do fundo preenchido com `fill`. Ajuste `fill` para a cor da parede.
- **Borda ou halo em volta da pessoa** → recorte com fundo muito parecido com a roupa/cabelo; use
  `--quality best` no remove-background ou aceite (em 15 s quase não se nota).
- **Pulo na emenda do corte** → coloque o `glass.in` (ou um soco de câmera) exatamente no tempo da emenda.

## Desempenho
- **Render trava ou falha por memória** → `-w 1`. Feche outros apps pesados.
- **Recorte (remove-background) lento** → é normal: ~0,3–0,8 s por quadro. Rode em segundo plano.

## Instalação
- **Pediram para rodar `npx hyperframes skills`** (o CLAUDE.md que o `hyperframes init` cria sugere) → não rode;
  instalaria skills globais no Claude Code da pessoa. O `setup_project.py` troca esse CLAUDE.md por uma nota da skill.
