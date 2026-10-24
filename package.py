#!/usr/bin/env python3
"""Build the sellable item: the plugin/ folder (committed, used by the marketplace)
and a .zip of it in releases/ (the file you upload to your store or send to a tester).

    python package.py            -> plugin/  and  releases/refine-loop-<version>.zip

The plugin holds the reviewer agent, the refiner agent and the /refine skill.
Buyers use it with:
    claude --plugin-dir refine-loop.zip                 (one session)
    claude plugin marketplace add <your private repo>   (installed, gets updates)
    claude plugin install refine-loop@<marketplace>
"""

import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "refine-loop"
VERSION = "1.0.0"
DIST = ROOT / "releases"

MANIFEST = {
    "name": NAME,
    "version": VERSION,
    "description": "Every answer is drafted, checked by an independent reviewer agent, "
                   "and revised before you see it. /refine for one message, "
                   "`claude --agent refine-loop:refiner` for a whole session.",
    "author": {"name": "Your Name"},
    "keywords": ["review", "quality", "refine", "subagent"],
}


def build():
    out = ROOT / "plugin"
    shutil.rmtree(out, ignore_errors=True)
    DIST.mkdir(exist_ok=True)
    (out / ".claude-plugin").mkdir(parents=True)
    (out / ".claude-plugin" / "plugin.json").write_text(json.dumps(MANIFEST, indent=2) + "\n")
    shutil.copytree(ROOT / ".claude" / "agents", out / "agents")
    shutil.copytree(ROOT / ".claude" / "skills", out / "skills")
    shutil.copy2(ROOT / "LICENSE.md", out / "LICENSE.md") if (ROOT / "LICENSE.md").exists() else None
    (out / "README.md").write_text(f"""# Refine Loop {VERSION}

Every answer goes draft -> independent reviewer -> revise before you see it.

## Use it
- One message:      type `/refine <your request>` in Claude Code
- Rounds:           `/refine -r 3 <request>` (`-r 0` = no review). Default is 2.
- Whole session:    `claude --agent refine-loop:refiner`

## Install
- Try it once:      `claude --plugin-dir {NAME}-{VERSION}.zip`   (from the folder that holds the zip)
- Keep it:          `claude plugin marketplace add <marketplace you were given>`
                    `claude plugin install {NAME}@<marketplace>`
- Remove it:        `claude plugin uninstall {NAME}@<marketplace>`

## Settings
- Default rounds and stop-early: `skills/refine/SKILL.md`, the "Settings" lines
- What the reviewer checks:      `agents/reviewer.md`
""")

    zip_path = DIST / f"{NAME}-{VERSION}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(out))
    print(f"built  {out}/\nbuilt  {zip_path}  ({zip_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
