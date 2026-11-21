# Refine Loop

**Every answer is checked by an independent reviewer agent before you see it.**
Main agent drafts → reviewer agent critiques → main agent revises. Twice by default. Then you get the final answer.

Works in **Claude Code** and **GitHub Copilot** (CLI and VS Code). Runs on your existing subscription. Five text files, no code, MIT license.

```
your message
   │
   ▼
Main agent ── draft ──► Reviewer agent (fresh context, every round)
   ▲                         │
   └──── feedback ◄──────────┘     repeat N times (default 2)
   │
   ▼
final answer
```

---

## Install

**Claude Code** (2.1.224+; `claude update` if older)
```bash
claude plugin marketplace add cdandgey5/AgentOrchestration
claude plugin install refine-loop@refine-loop-market
```
Try without installing: download `releases/refine-loop-1.1.0.zip` and run `claude --plugin-dir refine-loop-1.1.0.zip` from that folder.

**GitHub Copilot**
```bash
copilot plugin install cdandgey5/AgentOrchestration:plugin
```

Both installs are user-wide: every folder, every project, including the Claude Desktop app's Code tab and VS Code.

## Use

| | Claude Code | Copilot |
|---|---|---|
| One message, reviewed | `/refine <request>` | `Use the /refine skill: <request>` |
| Set rounds for that message | `/refine -r 3 <request>` (`-r 0` = no review) | same, after the skill name |
| Every message, whole session | `claude --agent refine-loop:refiner` | `copilot --agent refiner` (VS Code: pick **refiner** in the agents dropdown) |
| Skip one message in session mode | `-r 0 <message>` | same |
| Remove | `claude plugin uninstall refine-loop@refine-loop-market` | `copilot plugin uninstall refine-loop` |

Each answer prints one status line per round, like `Round 1/2: reviewer said REVISE, 3 issues, fixed 3.`, then the answer, then a 3-bullet review log.

**Expect 2N+1 model calls per answer** (5 with the default). That is 3-5x the usage of a normal answer, on your own plan's limits. Use `-r 1` for everyday questions and 2+ for things where mistakes cost you: plans, code, research, emails.

## Change the defaults

| What | Where |
|---|---|
| Default rounds | `Default rounds: 2` in `skills/refine/SKILL.md` |
| Stop early when the reviewer approves | `Stop early ...: no` → `yes`, same file |
| What the reviewer checks, how strict | `agents/reviewer.md` (the Copilot copy is generated from it) |
| Reviewer model (Copilot) | add `model: <name>` to `com.github.copilot/agents/reviewer.agent.md`. A different model than the author is a good idea. |
| Reviewer model (Claude) | `model: inherit` → `model: opus` in `agents/reviewer.md` |

Edit the installed copy for a quick local change, or fork the repo, edit `.claude/...`, run `python package.py`, and install from your fork.

## Security

Read [SECURITY.md](SECURITY.md) before suggesting this at work. Short version:
- No code runs. It is instructions for the model, readable in full in 5 minutes.
- **Not offline.** Your prompts go to Anthropic or GitHub exactly as they do without this plugin. No new destination; more tokens.
- The reviewer agent can only read and search. It cannot change files or run commands.
- Ships no hooks, no MCP servers, no settings changes, no pre-approved permissions.
- `releases/SHA256SUMS` lets you verify the zip.

## How it works

- `skills/refine/SKILL.md`: the loop steps. Same file format in Claude Code and Copilot.
- `agents/reviewer.md`: the reviewer. Runs as a subagent with a fresh context, so it never sees the earlier reviews and cannot be talked into agreeing.
- `agents/refiner.md`: a session agent that runs the loop on every message.
- `plugin/`: the installable plugin, built by `package.py` from the files above. Two manifests (Claude: `.claude-plugin/plugin.json`, Copilot: `plugin.json`), shared skill, per-tool agent files.

## Extras (Claude Code only, need Python 3.8+)

- `chat.py`: a terminal chat where the loop runs in code, so it always does exactly N rounds and logs every draft and review to `logs/`. `python3 chat.py -r 3`, `/help` inside. Settings in `config.json`. It refuses to run on an API key by default (`subscription_only`).
- `demo/compare.py "<prompt>"`: runs one prompt through plain Claude Code and through the loop, writes a side-by-side `.md` and `.html`. See `demo/examples/`.
- `install.py`: copies the agents and skill into `~/.claude` without the plugin system.

## Contribute

Edit the sources in `.claude/`, bump `VERSION` in `package.py`, run `python package.py`, commit `plugin/` and `releases/`. Test with [TESTING.md](TESTING.md). Copilot support is new and untested by the author: reports welcome.

## Troubleshooting

| Problem | Fix |
|---|---|
| `/refine` not found (Claude) | `claude plugin list` shows it? If not, redo Install. Restart Claude Code after installing. |
| Skill not loading (Copilot) | Write it out: `Use the refine skill: ...`. Check `/skills list`. |
| Reviewer did not run as a separate agent | Claude: `/agents` must list `refine-loop:reviewer`. Copilot: `/agent` must list `reviewer`; the main agent needs the `agent` tool enabled. |
| `unknown option` | Update the tool: `claude update` / `copilot update` |
| Too slow | `-r 1`, or remove web tools from the reviewer |
| Usage-limit error | Your plan's limit. Wait, or lower rounds. |
