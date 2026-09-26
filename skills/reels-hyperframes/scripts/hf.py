#!/usr/bin/env python3
"""Roda o HyperFrames (versão testada) dentro do projeto, sem telemetria, sem checar atualização,
sem instalar skills globais e sem mandar quadros para IA de terceiros no snapshot.

Uso:
  python3 hf.py <pasta-de-trabalho> <comando> [opções do HyperFrames]
Exemplos:
  python3 hf.py "$WORK" check
  python3 hf.py "$WORK" snapshot --at 1.9,3.6,5.4 --no-end -o snaps
  python3 hf.py "$WORK" render -f 30 -q high -w 2 -o renders/reel.mp4
  python3 hf.py "$WORK" remove-background assets/footage.mp4 -o assets/person.webm --background-output assets/plate.webm
"""

import os
import subprocess
import sys

from common import HF, HF_ENV, die, work_paths


def main():
    if len(sys.argv) < 3:
        die(__doc__)
    p = work_paths(sys.argv[1])
    if not (p["project"] / "hyperframes.json").exists():
        die(f"não achei o projeto em {p['project']} — rode setup_project.py antes.")
    local = p["project"] / "node_modules" / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes")
    cmd = ([str(local)] if local.exists() else HF) + sys.argv[2:]
    env = os.environ.copy()
    env.update(HF_ENV)
    env.pop("GEMINI_API_KEY", None)  # sem isso, o snapshot mandaria os quadros para o Gemini
    print("$ hyperframes " + " ".join(sys.argv[2:]), file=sys.stderr)
    sys.exit(subprocess.run(cmd, cwd=p["project"], env=env).returncode)


if __name__ == "__main__":
    main()
