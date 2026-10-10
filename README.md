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
6. encaixa todo texto, cartão e painel na **área segura do Reels** (nada embaixo da interface do
   Instagram nem cortado em celular alto, como o iPhone 16);
7. confere os quadros em cada troca de efeito, ajusta posições e renderiza o MP4 1080×1920;
8. (opcional) dá o acabamento: borrão de movimento nos socos de câmera e grão de filme.

Faz Reels curto (~15 s, escolhendo o melhor trecho) ou edita o **vídeo inteiro** (30–60 s). Também
funciona com **gravação de tela narrada** (modo tela: corta a região certa da tela, tira barra de
menu e notificações, e põe os efeitos por cima).

## Novidades da v1.4 — narração com voz gerada (você escolhe a voz)

- vídeo sem fala, com áudio ruim ou que você quer narrado: o Claude escreve o roteiro com você e gera a
  voz com o **motor de voz da Microsoft** (o mesmo do Edge);
- você ouve **amostras de cada voz** (Antonio, Francisca, Thalita e outras) e escolhe — a skill não
  escolhe por você;
- a legenda sai com o **tempo exato de cada palavra**: nada de refazer a voz no CapCut e ressincronizar;
- a voz robótica de antes (o `tts` do HyperFrames, modelo Kokoro) não é mais usada;
- detalhes em `skills/reels-hyperframes/references/narration.md`.

## Novidades da v1.3 — área segura (100% legível em qualquer celular)

No teste publicado, vários elementos ficavam embaixo da interface do Instagram ou cortados: palavra
gigante atrás do cabeçalho "Reels", cartões e tabela cortados nas laterais e legenda longa embaixo do
botão de curtir. Em tela mais alta que 9:16 (iPhone 16, Android 20:9) o Instagram dá zoom para preencher
a altura e perde ~100 px de cada lado. Agora:

- o modelo mede cada texto com a fonte carregada e **encaixa tudo na área segura** antes do render:
  topo a partir de y 300, laterais entre x 120 e 960, coluna de botões livre (x > 860 abaixo de y 900),
  legendas em y 1170–1290 — contando até o zoom dos socos de câmera;
- texto que não cabe diminui a fonte sozinho (e o check avisa se precisar encurtar);
- palavra gigante e balões ganharam o modo **na frente da pessoa** (`"front": true`), o certo para close;
  palavra gigante configurada "acima da cabeça" (que caía embaixo do cabeçalho) vira "na frente" sozinha;
- a revisão gera a folha **`celular.jpg`**, com as faixas onde o Instagram cobre ou corta marcadas em
  vermelho;
- detalhes e números em `skills/reels-hyperframes/references/safe-zone.md`.

Projetos feitos com a versão anterior: é só gerar o `index.html` de novo e renderizar.

## Efeitos

- **Balões de pergunta** surgindo por trás da pessoa ("todo mundo me pergunta…")
- **Símbolo gigante** girando em 3D por trás (?, !, $)
- **Palavra gigante** batendo por trás da cabeça, com soco de câmera
- **Camadas de vidro 3D**: a cena gira e se separa em fundo / cartão / pessoa, depois junta de novo
- **Moldura + painel**: a pessoa vai para uma moldura e aparecem manchete e cartões ao lado
- **Anel de porcentagem** enchendo por trás da cabeça, com contador na legenda
- **Ilustração explicativa**: um painel com desenho (SVG) que vai se montando no tempo da fala
- **Tabela / ranking**: posições entrando uma a uma, com a campeã em dourado
- **Palavra gigante na frente** da pessoa, para vídeos em que a cabeça ocupa o topo da tela
- **Legenda palavra por palavra** com destaques em amarelo, verde e vermelho
- **Efeitos sonoros** automáticos (whoosh, pop, impacto, riser, brilho)
- **Narração com voz gerada** (motor da Microsoft): você escolhe a voz ouvindo amostras; legenda sincronizada
- **Acabamento opcional**: borrão de movimento e grão de filme; limpeza leve de ruído na voz

Exemplo: o config completo do Reels feito a partir do vídeo
[A Appmax é um gateway seguro?](https://www.youtube.com/watch?v=3Y6isKPyReU) está em
`skills/reels-hyperframes/assets/config.example.json`.

## Requisitos

- [Claude Code](https://claude.com/claude-code)
- **Node.js 22+**, **FFmpeg**, **Python 3**
- **yt-dlp** (para vídeos do YouTube)
- Um motor de transcrição: `mlx-whisper` (Mac com chip Apple), `faster-whisper` ou `whisper-cpp`
- Só para narração com voz gerada: `edge-tts` (`pip3 install edge-tts`) e internet

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

## Atualizar para a versão mais nova

**Se instalou como plugin (opção 1)**, dentro do Claude Code: `/plugin` → aba **Installed** →
`reels-hyperframes` → **Update now**. Ou, no terminal:
```bash
claude plugin update reels-hyperframes@reels-hyperframes
```
Depois rode `/reload-plugins` (ou abra uma sessão nova). Para receber as próximas versões sozinho:
`/plugin` → aba **Marketplaces** → `reels-hyperframes` → **Enable auto-update**.

**Se copiou a pasta (opção 2)**, na pasta onde você clonou o repositório:
```bash
cd reels-hyperframes && git pull
```
```bash
rm -rf ~/.claude/skills/reels-hyperframes && cp -r skills/reels-hyperframes ~/.claude/skills/
```

**Ou só peça ao Claude**, do seu jeito:

> atualiza minha skill reels-hyperframes com a versão mais nova do GitHub (ablynow1/reels-hyperframes)

Para saber se já está na v1.4: a pasta da skill tem o arquivo `scripts/narrate.py`.

## Como usar

Peça do seu jeito, por exemplo:

> faz um reels de 15s desse vídeo meu e deixa a edição foda pra postar no instagram: https://www.youtube.com/watch?v=...

> pega o trecho em que eu falo do preço e transforma num short

Um Reels leva uns 15–30 min na primeira vez (a maior parte é transcrição e recorte da pessoa).
O vídeo final fica em `reels-<assunto>/project/renders/reel.mp4`.

## Quanto custa
Quase tudo roda no seu computador: download, transcrição (Whisper local), recorte da pessoa (IA local)
e render (Chrome + FFmpeg). Nenhuma API paga é chamada. O que gasta tokens do Claude é o raciocínio:
ler a transcrição, escolher o trecho, montar o roteiro e olhar os quadros — um Reels completo com
ajustes fica na casa de algumas centenas de milhares de tokens.

## Bom saber

- Use só vídeos seus ou com permissão.
- O texto na tela sai do que a pessoa fala; a skill não inventa números.
- Nada é instalado de forma global: o HyperFrames fica dentro da pasta do projeto e roda sem telemetria
  e sem checagem de atualização (variáveis de ambiente, nada gravado fora do projeto).
- Vídeo de origem em 720p fica um pouco mais suave que uma gravação vertical nativa.

## Créditos

- [HyperFrames](https://github.com/heygen-com/hyperframes) — Apache 2.0.
- Efeitos sonoros: vêm dentro do pacote do HyperFrames (Pixabay Content License) e são copiados para o
  seu projeto na instalação; não são redistribuídos por este repositório.
- Fontes Montserrat e Bebas Neue (Google Fonts), resolvidas pelo HyperFrames.
- Ideias de revisão em cada troca de cena e de borrão de movimento por subquadros vieram do
  [pdoom-video](https://github.com/mexicat/pdoom-video) (MIT).

## Licença

MIT — veja `LICENSE`.
