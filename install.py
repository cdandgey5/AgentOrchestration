#!/usr/bin/env python3
"""Install the reviewer subagent and /refine command for ALL your projects.

Copies them into ~/.claude (or $CLAUDE_CONFIG_DIR). An existing file with
different content is backed up as <name>.bak first.

    python install.py              install / update
    python install.py --uninstall  remove (and restore any .bak)
"""

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
FILES = [
    (ROOT / ".claude/agents/reviewer.md", HOME / "agents/reviewer.md"),
    (ROOT / ".claude/agents/refiner.md", HOME / "agents/refiner.md"),
    (ROOT / ".claude/skills/refine/SKILL.md", HOME / "skills/refine/SKILL.md"),
]


def install():
    for src, dst in FILES:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and dst.read_bytes() != src.read_bytes():
            shutil.copy2(dst, dst.with_name(dst.name + ".bak"))
            print(f"backed up  {dst}.bak")
        shutil.copy2(src, dst)
        print(f"installed  {dst}")

    chat = ROOT / "chat.py"
    print("\nDone. In any project:")
    print("  one message reviewed:   start `claude`, type  /refine <your question>")
    print("  every message reviewed: run  claude --agent refiner")
    print("\nOptional shortcut for the chat script:")
    if os.name == "nt":
        print(f"  PowerShell: add to $PROFILE ->  function rchat {{ python \"{chat}\" @args }}")
    else:
        print(f"  add to ~/.zshrc or ~/.bashrc ->  alias rchat='python3 \"{chat}\"'")


def uninstall():
    for _, dst in FILES:
        backup = dst.with_name(dst.name + ".bak")
        if dst.exists():
            dst.unlink()
            print(f"removed    {dst}")
        if backup.exists():
            backup.rename(dst)
            print(f"restored   {dst}")
    skill_dir = HOME / "skills/refine"
    if skill_dir.exists() and not any(skill_dir.iterdir()):
        skill_dir.rmdir()


if __name__ == "__main__":
    uninstall() if "--uninstall" in sys.argv else install()
