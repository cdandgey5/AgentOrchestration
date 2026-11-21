#!/usr/bin/env python3
"""Build the plugin that works in BOTH Claude Code and GitHub Copilot.

    python package.py   -> plugin/  (committed; what `plugin install` reads)
                           releases/refine-loop-<version>.zip  (for `claude --plugin-dir`)
                           releases/SHA256SUMS

Single source of truth: .claude/agents/*.md and .claude/skills/refine/SKILL.md.
Copilot's agent files (*.agent.md) are generated from them, so the two never drift.

Layout of plugin/ (one folder, two readers):
    .claude-plugin/plugin.json          Claude Code manifest
    plugin.json                         Copilot manifest (Agent Plugins 1.0)
    skills/refine/SKILL.md              shared: same format in both tools
    agents/reviewer.md, refiner.md      Claude Code agents
    com.github.copilot/agents/*.agent.md   Copilot agents (Claude ignores this folder)
"""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "refine-loop"
VERSION = "1.1.0"
AUTHOR = "cdandgey5"
REPO_URL = "https://github.com/cdandgey5/AgentOrchestration"
DESCRIPTION = ("Every answer is drafted, checked by an independent reviewer agent, and revised "
               "before you see it. /refine for one message, a 'refiner' agent for a whole session.")
RELEASES = ROOT / "releases"
SRC_AGENTS = ROOT / ".claude" / "agents"
SRC_SKILLS = ROOT / ".claude" / "skills"

# Copilot tool aliases: read/search/web only for the reviewer, so it can never change
# files or run commands. The refiner is the main agent and keeps the normal tool set.
COPILOT_FRONTMATTER = {
    "reviewer": '---\nname: reviewer\ndescription: {description}\ntools: ["read", "search", "web"]\n---\n',
    "refiner": '---\nname: refiner\ndescription: {description}\n---\n',
}
COPILOT_REFINER_DESCRIPTION = ("Always-on refine mode for a whole session. Every answer goes draft -> "
                               "reviewer agent -> revise before the user sees it. Start it with "
                               "`copilot --agent refiner`, or pick it in the VS Code agents dropdown.")
COPILOT_REFINER_PREAMBLE = """You are in REFINE MODE. Every answer you give must go through the refine loop below.
Do this for every message, even short or simple ones. The user can type "-r 0 <message>" to skip the review for that message.
"""


def split_frontmatter(text):
    """Return (frontmatter dict, body) for a markdown file with a YAML header."""
    meta, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            body = text[end + 4:].lstrip("\n")
    return meta, body


def copilot_agent(name, skill_body):
    meta, body = split_frontmatter((SRC_AGENTS / f"{name}.md").read_text(encoding="utf-8"))
    if name == "refiner":
        # Copilot has no "load this skill" tool, so the loop steps are embedded from SKILL.md.
        meta["description"] = COPILOT_REFINER_DESCRIPTION
        settings = skill_body.split("## Steps", 1)[0].split("Settings", 1)[1].split("\n\n", 1)[0]
        body = (COPILOT_REFINER_PREAMBLE + "\nSettings" + settings + "\n\n"
                "The **request** is the user's whole message.\n\n## Steps\n\n"
                + skill_body.split("## Steps", 1)[1].lstrip("\n"))
    head = COPILOT_FRONTMATTER[name].format(description=meta["description"])
    return head + "\n" + body


def build():
    out = ROOT / "plugin"
    shutil.rmtree(out, ignore_errors=True)
    RELEASES.mkdir(exist_ok=True)

    # Shared skill and Claude agents: straight copies.
    shutil.copytree(SRC_SKILLS, out / "skills")
    shutil.copytree(SRC_AGENTS, out / "agents")
    shutil.copy2(ROOT / "LICENSE", out / "LICENSE")

    # Copilot agents, generated.
    _, skill_body = split_frontmatter((SRC_SKILLS / "refine" / "SKILL.md").read_text(encoding="utf-8"))
    cp_agents = out / "com.github.copilot" / "agents"
    cp_agents.mkdir(parents=True)
    for name in ("reviewer", "refiner"):
        (cp_agents / f"{name}.agent.md").write_text(copilot_agent(name, skill_body), encoding="utf-8")

    # Two manifests.
    common = {"name": NAME, "version": VERSION, "description": DESCRIPTION,
              "author": {"name": AUTHOR}, "license": "MIT", "repository": REPO_URL,
              "keywords": ["review", "quality", "refine", "subagent"]}
    (out / ".claude-plugin").mkdir()
    (out / ".claude-plugin" / "plugin.json").write_text(json.dumps(common, indent=2) + "\n")
    (out / "plugin.json").write_text(json.dumps(
        {"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", **common}, indent=2) + "\n")

    (out / "README.md").write_text(f"""# Refine Loop {VERSION}

Every answer goes draft -> independent reviewer agent -> revise before you see it.
Works in Claude Code and GitHub Copilot. Five text files, no code. MIT license.

## Claude Code
- Try once:    `claude --plugin-dir {NAME}-{VERSION}.zip`
- Install:     `claude plugin marketplace add {AUTHOR}/AgentOrchestration`
               `claude plugin install {NAME}@refine-loop-market`
- One message: `/refine <request>`   rounds: `/refine -r 3 <request>` (`-r 0` = no review)
- Session:     `claude --agent {NAME}:refiner`
- Remove:      `claude plugin uninstall {NAME}@refine-loop-market`

## GitHub Copilot (CLI, VS Code)
- Install:     `copilot plugin install {AUTHOR}/AgentOrchestration:plugin`
- One message: `Use the /refine skill: <request>`
- Session:     `copilot --agent refiner`   (VS Code: pick "refiner" in the agents dropdown)
- Remove:      `copilot plugin uninstall {NAME}`

## Settings
- Default rounds, stop-early: `skills/refine/SKILL.md`, the "Settings" lines
- What the reviewer checks:   `agents/reviewer.md` (Claude) and `com.github.copilot/agents/reviewer.agent.md` (Copilot)

Security notes: {REPO_URL}/blob/main/SECURITY.md
""", encoding="utf-8")

    # Zip + checksums. Old zips go, so SHA256SUMS always matches what is in the folder.
    for old in RELEASES.glob("*.zip"):
        old.unlink()
    zip_path = RELEASES / f"{NAME}-{VERSION}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(out))
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (RELEASES / "SHA256SUMS").write_text(f"{digest}  {zip_path.name}\n")

    print(f"built  {out}/")
    for f in sorted(out.rglob("*")):
        if f.is_file():
            print(f"       {f.relative_to(out)}")
    print(f"built  {zip_path}  ({zip_path.stat().st_size // 1024} KB)\nsha256 {digest}")


if __name__ == "__main__":
    build()
