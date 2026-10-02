#!/usr/bin/env python3
"""Refine chat: every answer goes draft -> reviewer -> revise, N rounds.

Runs on Claude Code's headless mode (`claude -p`), so it uses your existing
Claude Code login. Python 3.8+, no extra packages.

    python chat.py                    chat, 2 review rounds per answer
    python chat.py -r 3               chat, 3 review rounds per answer
    python chat.py "your question"    one answer, then exit
    python chat.py --steps            also print every draft and review
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "prompts"
REVIEWER_AGENT = ROOT / ".claude" / "agents" / "reviewer.md"

DEFAULTS = {
    "rounds": 2,
    "stop_early": False,
    "show_steps": False,
    "main_model": None,
    "reviewer_model": None,
    "main_tools": "Read,Grep,Glob,WebSearch,WebFetch",
    "reviewer_tools": "Read,Grep,Glob,WebSearch,WebFetch",
    "history_turns": 3,
    "log_dir": "logs",
    "timeout_seconds": 600,
}

HELP = """Commands:
  /rounds N   set review rounds per answer (0 = no review)
  /steps      show or hide drafts and reviews
  /early      stop a loop early when the reviewer says APPROVE (on/off)
  /new        start a new conversation
  /help       show this help
  /exit       quit
  \"\"\"         start or end a multi-line message"""


class ClaudeError(Exception):
    pass


# ---------- small helpers ----------

def status(msg):
    """Progress line on stderr, so stdout holds only answers."""
    print(f"  {msg}", file=sys.stderr, flush=True)


def fill(template, **values):
    """Replace {name} placeholders in one pass (inserted text is never rescanned)."""
    return re.sub(r"\{(\w+)\}", lambda m: str(values.get(m.group(1), m.group(0))), template)


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip("\n")
    return text


def parse_verdict(review):
    found = re.findall(r"VERDICT:\s*\**\s*(APPROVE|REVISE)", review, re.IGNORECASE)
    return found[-1].upper() if found else "REVISE"  # last one wins if it changed its mind


def count_issues(review):
    return len(re.findall(r"^\s*\d+\.\s", review, re.MULTILINE))


def load_config(path, args):
    cfg = dict(DEFAULTS)
    path = Path(path)
    if path.exists():
        try:
            cfg.update(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            sys.exit(f"config error in {path}: {e}")
    if args.rounds is not None:
        cfg["rounds"] = args.rounds
    if args.steps:
        cfg["show_steps"] = True
    if args.stop_early:
        cfg["stop_early"] = True
    if args.main_model:
        cfg["main_model"] = args.main_model
    if args.reviewer_model:
        cfg["reviewer_model"] = args.reviewer_model
    if not isinstance(cfg["rounds"], int) or cfg["rounds"] < 0:
        sys.exit("rounds must be a whole number, 0 or more")
    return cfg


class Spinner:
    """Shows '| Reviewer 1/2 (12s)' while a call runs. Silent when not a terminal."""

    def __init__(self, label):
        self.label = label
        self.done = threading.Event()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.active = sys.stderr.isatty()

    def _spin(self):
        start, i, frames = time.time(), 0, "|/-\\"
        while not self.done.wait(0.2):
            sys.stderr.write(f"\r  {frames[i % 4]} {self.label} ({int(time.time() - start)}s) ")
            sys.stderr.flush()
            i += 1

    def __enter__(self):
        if self.active:
            self.thread.start()
        return self

    def __exit__(self, *exc):
        self.done.set()
        if self.active:
            self.thread.join()
            sys.stderr.write("\r" + " " * (len(self.label) + 16) + "\r")
            sys.stderr.flush()


class Log:
    """Markdown transcript of every draft, review and final answer."""

    def __init__(self, log_dir):
        self.path = None
        if log_dir:
            folder = Path(log_dir)
            if not folder.is_absolute():
                folder = ROOT / folder
            folder.mkdir(parents=True, exist_ok=True)
            self.path = folder / f"{datetime.now():%Y-%m-%d_%H%M%S}.md"

    def write(self, text):
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(text)

    def section(self, title, body):
        self.write(f"\n### {title}\n\n{body}\n")


# ---------- claude -p wrapper ----------

class Claude:
    def __init__(self, timeout):
        self.exe = shutil.which("claude")
        if not self.exe:
            sys.exit("Claude Code CLI not found. Install it, run `claude` once to log in, then retry.")
        self.timeout = timeout
        # Don't inherit the session id when started from inside a Claude Code terminal.
        self.env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}

    def run(self, prompt, *, system_file, tools, model, session=None, resume=False):
        """One headless Claude call. Returns (text, cost_usd).

        session=None  -> throwaway context (used for every reviewer call)
        session=<id>  -> persistent main-agent conversation
        """
        cmd = [self.exe, "-p", "--output-format", "json",
               "--append-system-prompt-file", str(system_file),
               "--tools", tools or ""]
        if tools:
            cmd += ["--allowedTools", tools]
        if model:
            cmd += ["--model", model]
        if session:
            cmd += ["--resume" if resume else "--session-id", session]
        else:
            cmd += ["--no-session-persistence"]
        try:
            proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace",
                                  env=self.env, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise ClaudeError(f"claude timed out after {self.timeout}s (raise timeout_seconds in config.json)")
        data = self._parse(proc.stdout)
        if data is None:
            detail = (proc.stderr or proc.stdout).strip()[-1500:]
            hint = "\nIf it says 'unknown option', run `claude update`." if "unknown option" in detail else ""
            raise ClaudeError((detail or f"claude exited with code {proc.returncode}") + hint)
        if data.get("is_error"):
            raise ClaudeError(str(data.get("result") or data.get("subtype") or "unknown error"))
        return (data.get("result") or "").strip(), float(data.get("total_cost_usd") or 0)

    @staticmethod
    def _parse(stdout):
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            for line in reversed(stdout.splitlines()):
                if line.startswith("{"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        pass
        return None


# ---------- the loop ----------

class RefineChat:
    def __init__(self, cfg, claude, reviewer_file):
        self.cfg = cfg
        self.claude = claude
        self.reviewer_file = reviewer_file
        self.main_file = PROMPTS / "main.md"
        self.review_tpl = (PROMPTS / "review.md").read_text(encoding="utf-8")
        self.revise_tpl = (PROMPTS / "revise.md").read_text(encoding="utf-8")
        self.log = Log(cfg["log_dir"])
        self.new()

    def new(self):
        self.session = str(uuid.uuid4())
        self.started = False
        self.history = []  # (request, final answer) of finished turns
        self.log.write(f"\n# Conversation {datetime.now():%Y-%m-%d %H:%M}\n"
                       f"Continue in Claude Code: `claude --resume {self.session}`\n")

    def _main(self, prompt):
        try:
            result = self.claude.run(prompt, system_file=self.main_file, tools=self.cfg["main_tools"],
                                     model=self.cfg["main_model"], session=self.session,
                                     resume=self.started)
        except ClaudeError:
            if not self.started:  # failed before the session existed: start clean next time
                self.session = str(uuid.uuid4())
            raise
        self.started = True
        return result

    def _review(self, request, draft):
        prompt = fill(self.review_tpl, history=self._history_text(), request=request, draft=draft)
        return self.claude.run(prompt, system_file=self.reviewer_file, tools=self.cfg["reviewer_tools"],
                               model=self.cfg["reviewer_model"])

    def _history_text(self):
        turns = self.history[-self.cfg["history_turns"]:] if self.cfg["history_turns"] else []
        if not turns:
            return "none (this is the first message)"
        parts = []
        for req, ans in turns:
            ans = ans if len(ans) <= 1500 else ans[:1500] + " [...]"
            parts.append(f"USER: {req}\nASSISTANT: {ans}")
        return "\n\n".join(parts)

    def _step(self, title, body, screen=True):
        self.log.section(title, body)
        if screen and self.cfg["show_steps"]:
            print(f"\n----- {title} -----\n{body}\n", file=sys.stderr, flush=True)

    def turn(self, request):
        rounds = self.cfg["rounds"]
        cost, start = 0.0, time.time()
        self.log.write(f"\n## Turn {len(self.history) + 1}\n")
        self._step("User", request, screen=False)

        with Spinner("Main agent: drafting"):
            answer, c = self._main(request)
        cost += c
        self._step("Draft", answer)

        done = 0
        for i in range(1, rounds + 1):
            with Spinner(f"Reviewer {i}/{rounds}: reviewing"):
                review, c = self._review(request, answer)
            cost += c
            verdict, issues = parse_verdict(review), count_issues(review)
            self._step(f"Review {i}/{rounds} ({verdict})", review)
            if self.cfg["stop_early"] and verdict == "APPROVE":
                status(f"round {i}/{rounds}: reviewer APPROVE -> stopping early")
                break
            with Spinner(f"Main agent: revising {i}/{rounds}"):
                answer, c = self._main(fill(self.revise_tpl, round=i, rounds=rounds, review=review))
            cost += c
            done = i
            status(f"round {i}/{rounds}: reviewer {verdict} ({issues} issues) -> revised")
            self._step(f"Revision {i}/{rounds}", answer, screen=i < rounds)  # last one = final answer

        self.history.append((request, answer))
        self.log.section("Final answer", answer)
        if self.cfg["show_steps"]:
            print("\n===== Final answer =====", file=sys.stderr, flush=True)
        print(f"\n{answer}\n", flush=True)
        status(f"[{done} revision(s) - {int(time.time() - start)}s - est. ${cost:.2f}]")
        return answer


# ---------- terminal UI ----------

def read_block():
    lines = []
    while True:
        line = input("... ")
        if line.strip() == '"""':
            return "\n".join(lines)
        lines.append(line)


def command(chat, text):
    """Handle /commands. Returns False to quit."""
    name, _, arg = text.partition(" ")
    name, arg = name.lower(), arg.strip()
    cfg = chat.cfg
    if name in ("/exit", "/quit", "/q"):
        return False
    if name == "/rounds":
        if arg.isdigit():
            cfg["rounds"] = int(arg)
        status(f"review rounds: {cfg['rounds']}")
    elif name == "/steps":
        cfg["show_steps"] = not cfg["show_steps"]
        status(f"show drafts and reviews: {'on' if cfg['show_steps'] else 'off'}")
    elif name == "/early":
        cfg["stop_early"] = not cfg["stop_early"]
        status(f"stop early on APPROVE: {'on' if cfg['stop_early'] else 'off'}")
    elif name == "/new":
        chat.new()
        status("new conversation started")
    else:
        print(HELP, file=sys.stderr)
    return True


def repl(chat):
    cfg = chat.cfg
    print(f"Refine chat - {cfg['rounds']} review round(s) per answer. /help for commands, /exit to quit.",
          file=sys.stderr)
    if chat.log.path:
        print(f"Log: {chat.log.path}", file=sys.stderr)
    while True:
        try:
            text = input("\nyou> ").strip()
            if text == '"""':
                text = read_block().strip()
        except (EOFError, KeyboardInterrupt):
            print(file=sys.stderr)
            break
        if not text:
            continue
        if text.startswith("/"):
            if not command(chat, text):
                break
            continue
        try:
            chat.turn(text)
        except ClaudeError as e:
            print(f"\n  ERROR: {e}", file=sys.stderr)
        except KeyboardInterrupt:
            print("\n  (cancelled)", file=sys.stderr)
    if chat.started:
        print(f"Continue this conversation in Claude Code: claude --resume {chat.session}", file=sys.stderr)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    p = argparse.ArgumentParser(description="Chat where every answer is reviewed and revised N times.")
    p.add_argument("prompt", nargs="*", help="ask one question and exit (use - to read it from stdin)")
    p.add_argument("-r", "--rounds", type=int, help="review rounds per answer (default from config.json)")
    p.add_argument("--steps", action="store_true", help="print every draft and review")
    p.add_argument("--stop-early", action="store_true", help="stop when the reviewer says APPROVE")
    p.add_argument("--main-model", help="model for the main agent, e.g. opus or sonnet")
    p.add_argument("--reviewer-model", help="model for the reviewer, e.g. opus or sonnet")
    p.add_argument("--config", default=str(ROOT / "config.json"), help="path to config.json")
    args = p.parse_args()

    cfg = load_config(args.config, args)
    claude = Claude(cfg["timeout_seconds"])

    # Reviewer instructions come from the same file Claude Code uses for the /refine subagent.
    reviewer_body = strip_frontmatter(REVIEWER_AGENT.read_text(encoding="utf-8"))
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    tmp.write(reviewer_body)
    tmp.close()

    try:
        chat = RefineChat(cfg, claude, Path(tmp.name))
        if args.prompt:
            question = sys.stdin.read() if args.prompt == ["-"] else " ".join(args.prompt)
            try:
                chat.turn(question.strip())
            except ClaudeError as e:
                sys.exit(f"ERROR: {e}")
        else:
            repl(chat)
    except KeyboardInterrupt:
        pass
    finally:
        os.unlink(tmp.name)


if __name__ == "__main__":
    main()
