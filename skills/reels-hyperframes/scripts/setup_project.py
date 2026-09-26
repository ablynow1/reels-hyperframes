#!/usr/bin/env python3
"""Cria o projeto HyperFrames em <pasta>/project (vertical 1080x1920), sem instalar nada global.

- NÃO instala as "skills" do HyperFrames no Claude Code (HYPERFRAMES_SKIP_SKILLS=1)
- instala o HyperFrames só dentro do projeto (node_modules, versão exata); telemetria desligada por
  variável de ambiente (nada é gravado fora da pasta do projeto)
- copia os efeitos sonoros que vêm no pacote do HyperFrames para project/assets/sfx

Uso:
  python3 setup_project.py <pasta-de-trabalho>
"""

import shutil
import sys

from common import DEFAULT_SFX, HF, HF_ENV, HF_VERSION, die, find_sfx_dir, need, run, work_paths

PROJECT_NOTE = """# Projeto gerado pela skill reels-hyperframes

- Não edite `index.html` à mão: edite `config.json` (e `captions.json`) e rode
  `python3 <skill>/scripts/build_composition.py <pasta-de-trabalho>`.
- Não rode `npx hyperframes skills` nem `skills update`: isso instalaria skills globais
  no Claude Code da pessoa. Tudo que a edição precisa já está na skill reels-hyperframes.
- Rode o HyperFrames sempre pelo `python3 <skill>/scripts/hf.py <pasta-de-trabalho> <comando>`
  (check, snapshot, render, remove-background): ele desliga telemetria e não instala nada global.
"""


def main():
    if len(sys.argv) != 2:
        die(__doc__)
    need("npx", "Instale o Node.js 22+ (ele traz o npx).")
    p = work_paths(sys.argv[1])
    p["work"].mkdir(parents=True, exist_ok=True)
    env = dict(HF_ENV)

    if not (p["project"] / "hyperframes.json").exists():
        run(HF + ["init", "project", "--resolution", "portrait", "--non-interactive"], cwd=p["work"], env=env)
    else:
        print("Projeto já existe, só conferindo dependências.")

    if not (p["project"] / "node_modules" / "hyperframes").exists():
        run(["npm", "install", "--no-audit", "--no-fund", "--save-dev", "--save-exact", f"hyperframes@{HF_VERSION}"], cwd=p["project"], env=env)

    # O CLAUDE.md/AGENTS.md que o init cria mandam instalar skills globais; trocamos por uma nota da skill
    for name in ("CLAUDE.md", "AGENTS.md"):
        (p["project"] / name).write_text(PROJECT_NOTE, encoding="utf-8")

    sfx_dst = p["assets"] / "sfx"
    sfx_dst.mkdir(parents=True, exist_ok=True)
    sfx_src = find_sfx_dir(p["project"])
    if not sfx_src:
        print("AVISO: não achei os efeitos sonoros do HyperFrames; o vídeo sai só com a voz.", file=sys.stderr)
    else:
        for f in DEFAULT_SFX:
            if (sfx_src / f).exists():
                shutil.copy2(sfx_src / f, sfx_dst / f)
    (p["project"] / "renders").mkdir(exist_ok=True)
    print(f"\nProjeto pronto: {p['project']}")


if __name__ == "__main__":
    main()
