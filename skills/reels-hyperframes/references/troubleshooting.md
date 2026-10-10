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
  Use as pausas do `words.py` para cortar; o `build_captions.py` encaixa o começo e o fim das palavras nas
  pausas reais do áudio.
- **Pausas demais ou de menos** → o limite de silêncio é calculado entre o ruído de fundo e a fala; em áudio
  muito ruidoso ele pode errar. Confira ouvindo o trecho ou pelos tempos das palavras.
- **Demora muito** → outras coisas pesadas rodando na máquina disputam a CPU. Espere, ou transcreva só um
  trecho: extraia com `ffmpeg -ss INICIO -t DURACAO` e ajuste os tempos.

## Check do HyperFrames
- **`media_missing_id`** → `<audio>` sem `id` sai MUDO no render. O builder já põe ids; não escreva áudio à mão.
- **`Font families used without @font-face declaration`** → fonte fora da lista automática (ex.: Anton, Impact).
  Use Montserrat, Bebas Neue, League Gothic, Oswald, Archivo Black, Poppins ou Inter.
- **`content_overlap` entre balões** → dois balões no mesmo lugar; mude `left`/`top`.
- **Contraste baixo** (símbolo claro em parede clara) → troque `color` do `bigSymbol` (veja "Fundo claro" em `effects.md`).
- **Contraste baixo nas legendas** (`#g1w1 1.94:1`) em fundo claro → pode ignorar: elas têm contorno preto,
  que o check não enxerga.
- **`composition_file_too_large`** → aviso esperado; pode ignorar.
- **`canvas_overflow` informativo** em texto gigante → normal quando o texto cresce na entrada (escala 1,8 → 1).

## Área segura (texto cortado ou embaixo da interface no celular)
- **No iPhone (ou em outro celular alto) texto some no topo, nas laterais ou embaixo dos botões** → é a área
  segura (`references/safe-zone.md`). Desde a v1.3 o modelo encaixa tudo sozinho; um projeto feito com
  versão antiga só precisa gerar de novo (`build_composition.py`) e renderizar. Confira no
  `snaps_review/celular.jpg`.
- **Check com `[área segura] … não coube … encurte o texto`** → texto comprido demais mesmo com a fonte
  reduzida: divida a legenda, encurte a palavra gigante ou tire linhas da tabela/etapas da ilustração.
- **Palavra gigante "por trás" escondida pela cabeça** → por trás ela fica a partir de y ≈ 300, e num close a
  cabeça está ali. Use `"front": true` (sem `top`: fica logo acima das legendas). Configs antigos com `top`
  acima de 300 (palavra "acima da cabeça") já viram "na frente" sozinhos.
- **Balão escondido atrás da cabeça** → menos espaço na lateral: use `width` 240–280, empilhe à esquerda,
  ou `"front": true` nos balões.
- **Painel de ilustração com texto pequeno** → o painel agora tem ~670–770 px úteis: redesenhe o SVG com
  `viewBox` de ~700 de largura e texto com 26 px ou mais.

## Narração (voz gerada)
- **`falta o edge-tts`** → `pip3 install edge-tts` (só é preciso para narrar).
- **Erro 403, "No audio was received" ou voz que não sai** → sem internet ou edge-tts desatualizado (a Microsoft
  muda o serviço de vez em quando): `pip3 install -U edge-tts`. Confira o nome da voz com `narrate.py --list`.
- **Palavra pronunciada errada** (inglês, marca, sigla) → escreva no roteiro do jeito que se fala
  (ex.: "guêituêis") e gere de novo; a legenda continua mostrando a palavra do roteiro como foi escrita.
- **Narração mais longa que o vídeo** → o `narrate.py` avisa; refaça o `make_clip.py` com um trecho maior
  ou encurte o roteiro.
- **Voz robótica** → é o `hyperframes tts` (Kokoro) ou o `say` do Mac; use o `narrate.py`.

## Visual
- **Balão/palavra sumiu** → está atrás da cabeça. Veja "Zonas da tela" em `effects.md` e mova para o lado ou use `"front": true`.
- **Legenda em 2 linhas** → bloco longo demais; divida em dois no `captions.json`.
- **Silhueta clara nas camadas de vidro** → é o buraco do fundo preenchido com `fill`. Ajuste `fill` para a cor da parede.
- **Borda ou halo em volta da pessoa** → recorte com fundo muito parecido com a roupa/cabelo; use
  `--quality best` no remove-background ou aceite (em 15 s quase não se nota).
- **Pulo na emenda do corte** → coloque o `glass.in` (ou um soco de câmera) exatamente no tempo da emenda.

## Desempenho
- **Render trava ou falha por memória** → `-w 1`. Feche outros apps pesados.
- **Recorte (remove-background) lento** → é normal: ~0,3–0,8 s por quadro. Rode em segundo plano.

## Vídeo sem pessoa
- **É gravação de tela, slides ou imagem parada** → avise a pessoa e siga `references/screen-recording.md`.
  Não rode o remove-background numa tela: ele recorta pedaços aleatórios da imagem.
- **Barra de menu, notificação ou agenda aparecendo** → corte fora com `make_clip.py --crop x,y,largura,altura`.

## Instalação
- **Pediram para rodar `npx hyperframes skills`** (o CLAUDE.md que o `hyperframes init` cria sugere) → não rode;
  instalaria skills globais no Claude Code da pessoa. O `setup_project.py` troca esse CLAUDE.md por uma nota da skill.
