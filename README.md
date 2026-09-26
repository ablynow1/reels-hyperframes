# reels-hyperframes

Skill para o **Claude Code** que transforma um vídeo de alguém falando pra câmera (link do YouTube ou
arquivo) num **Reels / Shorts / TikTok vertical de ~15 segundos** com edição de impacto, feita com o
[HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen, código aberto).

Você só pede, em português, e o Claude:

1. baixa o vídeo e transcreve a fala com o tempo de cada palavra;
2. escolhe o melhor trecho de ~15 s (gancho, ideia completa, número ou comparação);
3. corta, reenquadra em 9:16 e padroniza o volume da voz;
4. recorta a pessoa do fundo (IA local) para animar coisas **por trás dela**;
5. monta os efeitos em cima da fala, com legenda palavra por palavra e efeitos sonoros;
6. confere os quadros, ajusta posições e renderiza o MP4 1080×1920.

## Efeitos

- **Balões de pergunta** surgindo por trás da pessoa ("todo mundo me pergunta…")
- **Símbolo gigante** girando em 3D por trás (?, !, $)
- **Palavra gigante** batendo por trás da cabeça, com soco de câmera
- **Camadas de vidro 3D**: a cena gira e se separa em fundo / cartão / pessoa, depois junta de novo
- **Moldura + painel**: a pessoa vai para uma moldura e aparecem manchete e cartões ao lado
- **Anel de porcentagem** enchendo por trás da cabeça, com contador na legenda
- **Legenda palavra por palavra** com destaques em amarelo, verde e vermelho
- **Efeitos sonoros** automáticos (whoosh, pop, impacto, riser, brilho)

Exemplo: o config completo do Reels feito a partir do vídeo
[A Appmax é um gateway seguro?](https://www.youtube.com/watch?v=3Y6isKPyReU) está em
`skills/reels-hyperframes/assets/config.example.json`.

## Requisitos

- [Claude Code](https://claude.com/claude-code)
- **Node.js 22+**, **FFmpeg**, **Python 3**
- **yt-dlp** (para vídeos do YouTube)
- Um motor de transcrição: `mlx-whisper` (Mac com chip Apple), `faster-whisper` ou `whisper-cpp`

No Mac:
```bash
brew install node ffmpeg yt-dlp python
```
```bash
pip3 install mlx-whisper
```

A skill confere tudo isso sozinha antes de começar e diz o que falta.
Testada no macOS (Apple Silicon, 8 GB). No Windows, use pelo WSL.

## Instalação

**Opção 1 — plugin (recomendado).** Dentro do Claude Code:
```
/plugin marketplace add ablynow1/reels-hyperframes
```
```
/plugin install reels-hyperframes@reels-hyperframes
```

**Opção 2 — copiar a pasta da skill:**
```bash
git clone https://github.com/ablynow1/reels-hyperframes.git
```
```bash
mkdir -p ~/.claude/skills && cp -r reels-hyperframes/skills/reels-hyperframes ~/.claude/skills/
```

Depois abra uma sessão nova do Claude Code.

## Como usar

Peça do seu jeito, por exemplo:

> faz um reels de 15s desse vídeo meu e deixa a edição foda pra postar no instagram: https://www.youtube.com/watch?v=...

> pega o trecho em que eu falo do preço e transforma num short

Um Reels leva uns 15–30 min na primeira vez (a maior parte é transcrição e recorte da pessoa).
O vídeo final fica em `reels-<assunto>/project/renders/reel.mp4`.

## Bom saber

- Use só vídeos seus ou com permissão.
- O texto na tela sai do que a pessoa fala; a skill não inventa números.
- Nada é instalado de forma global: o HyperFrames fica dentro da pasta do projeto e a telemetria dele é desligada.
- Vídeo de origem em 720p fica um pouco mais suave que uma gravação vertical nativa.

## Créditos

- [HyperFrames](https://github.com/heygen-com/hyperframes) — Apache 2.0.
- Efeitos sonoros: vêm dentro do pacote do HyperFrames (Pixabay Content License) e são copiados para o
  seu projeto na instalação; não são redistribuídos por este repositório.
- Fontes Montserrat e Bebas Neue (Google Fonts), resolvidas pelo HyperFrames.

## Licença

MIT — veja `LICENSE`.
