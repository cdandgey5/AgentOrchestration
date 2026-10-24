#!/usr/bin/env python3
"""Side-by-side demo: Claude Code as-is vs. the same prompt through the refine loop.

Writes demo/out/<timestamp>-<slug>.md and .html with:
  Case 1  plain `claude -p` (same model, same tools)
  Case 2  refine loop (draft -> reviewer -> revise, N rounds)
  plus what the reviewer caught in each round.

    python demo/compare.py "your prompt"
    python demo/compare.py -r 3 "your prompt"
    python demo/compare.py -f prompt.txt
"""

import argparse
import html
import io
import re
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import chat  # noqa: E402  (the refine loop lives there)

OUT = ROOT / "demo" / "out"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "prompt"


def md_report(prompt, base, turn, rounds, model):
    lines = [
        f"# Claude Code as-is vs. Refine loop\n",
        f"*{datetime.now():%Y-%m-%d %H:%M} - model: {model or 'default'} - "
        f"refine rounds: {rounds} - refine calls: {turn['calls']} - refine time: {turn['seconds']}s*\n",
        "## Prompt\n", f"> {prompt.replace(chr(10), chr(10) + '> ')}\n",
        "## Case 1: Claude Code as-is\n", base, "",
        f"## Case 2: Same prompt, refine loop ({rounds} review rounds)\n", turn["final"], "",
        "## What the reviewer caught\n",
    ]
    for i, review in enumerate(turn["reviews"], 1):
        lines += [f"### Round {i}\n", "```", review, "```", ""]
    lines += ["## First draft (before any review)\n", turn["draft"], ""]
    return "\n".join(lines)


def html_report(prompt, base, turn, rounds, model):
    e = html.escape
    reviews = "".join(
        f"<h3>Round {i}</h3><pre>{e(r)}</pre>" for i, r in enumerate(turn["reviews"], 1))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claude Code as-is vs. Refine loop</title>
<style>
  body {{ margin: 0; padding: 24px; background: #0f1115; color: #e6e6e6;
         font-family: -apple-system, Segoe UI, Roboto, sans-serif; }}
  h1 {{ font-size: 24px; margin: 0 0 6px; }}
  .meta {{ color: #9aa0a6; font-size: 13px; margin-bottom: 20px; }}
  .prompt {{ background: #1a1d24; border-left: 4px solid #f5b942; padding: 12px 16px;
             border-radius: 6px; white-space: pre-wrap; margin-bottom: 24px; }}
  .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  @media (max-width: 900px) {{ .cols {{ grid-template-columns: 1fr; }} }}
  .card {{ background: #161920; border: 1px solid #2a2e37; border-radius: 10px; padding: 18px; }}
  .card h2 {{ margin: 0 0 12px; font-size: 17px; }}
  .base h2 {{ color: #9aa0a6; }}
  .refined {{ border-color: #3ddc84; }}
  .refined h2 {{ color: #3ddc84; }}
  pre {{ white-space: pre-wrap; word-wrap: break-word; font-family: ui-monospace, Menlo, Consolas, monospace;
         font-size: 13px; line-height: 1.5; margin: 0; }}
  details {{ margin-top: 24px; }}
  summary {{ cursor: pointer; color: #f5b942; font-weight: 600; }}
  h3 {{ font-size: 14px; color: #9aa0a6; margin: 16px 0 6px; }}
</style>
</head>
<body>
<h1>Claude Code as-is vs. Refine loop</h1>
<div class="meta">{e(f"{datetime.now():%Y-%m-%d %H:%M}")} &middot; model: {e(model or 'default')} &middot;
  refine: {rounds} review rounds, {turn['calls']} Claude calls, {turn['seconds']}s</div>
<div class="prompt">{e(prompt)}</div>
<div class="cols">
  <div class="card base"><h2>Case 1 &middot; Claude Code as-is</h2><pre>{e(base)}</pre></div>
  <div class="card refined"><h2>Case 2 &middot; Same prompt, refine loop</h2><pre>{e(turn['final'])}</pre></div>
</div>
<details><summary>What the reviewer caught</summary>{reviews}</details>
<details><summary>First draft, before any review</summary><pre>{e(turn['draft'])}</pre></details>
</body>
</html>
"""


def main():
    p = argparse.ArgumentParser(description="Compare Claude Code as-is with the refine loop.")
    p.add_argument("prompt", nargs="*", help="the prompt")
    p.add_argument("-f", "--file", help="read the prompt from a file")
    p.add_argument("-r", "--rounds", type=int, help="review rounds (default from config.json)")
    p.add_argument("--model", help="model for both cases, e.g. sonnet or opus")
    p.add_argument("--config", default=str(ROOT / "config.json"))
    args = p.parse_args()

    prompt = Path(args.file).read_text(encoding="utf-8").strip() if args.file else " ".join(args.prompt).strip()
    if not prompt:
        sys.exit("give a prompt, or -f file")

    cfg = chat.load_config(args.config, argparse.Namespace(
        rounds=args.rounds, steps=False, stop_early=False, main_model=args.model, reviewer_model=None))
    cfg["log_dir"] = None
    claude = chat.Claude(cfg["timeout_seconds"], cfg["subscription_only"])

    chat.status("Case 1: Claude Code as-is")
    with chat.Spinner("Claude Code as-is"):
        base = claude.run(prompt, system_file=None, tools=cfg["main_tools"], model=cfg["main_model"])

    chat.status(f"Case 2: refine loop, {cfg['rounds']} rounds")
    reviewer_body = chat.strip_frontmatter(chat.REVIEWER_AGENT.read_text(encoding="utf-8"))
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tmp:
        tmp.write(reviewer_body)
    try:
        loop = chat.RefineChat(cfg, claude, Path(tmp.name))
        with redirect_stdout(io.StringIO()):
            loop.turn(prompt, show=False)
    finally:
        Path(tmp.name).unlink()
    turn = loop.last_turn

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / f"{datetime.now():%Y-%m-%d_%H%M%S}-{slug(prompt)}"
    md, htm = stem.with_suffix(".md"), stem.with_suffix(".html")
    md.write_text(md_report(prompt, base, turn, cfg["rounds"], cfg["main_model"]), encoding="utf-8")
    htm.write_text(html_report(prompt, base, turn, cfg["rounds"], cfg["main_model"]), encoding="utf-8")
    print(f"\nCase 1 ({len(base)} chars) vs Case 2 ({len(turn['final'])} chars)")
    print(f"Markdown: {md}\nHTML:     {htm}")


if __name__ == "__main__":
    main()
