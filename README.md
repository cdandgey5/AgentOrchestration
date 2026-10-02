# Refine Loop for Claude Code

Every answer is checked by a reviewer before you see it.
**Main agent drafts → reviewer subagent critiques → main agent revises.** This repeats N times (default **2**). Then you get the final answer.

```
your prompt
   │
   ▼
Main agent ── draft ──► Reviewer (fresh context, every round)
   ▲                         │
   └──── feedback ◄──────────┘     repeat N times (default 2)
   │
   ▼
final answer
```

It runs on your **Claude subscription** (Pro, Max, Team or Enterprise) through the Claude Code CLI or app. There are **no API requests and no API key**, and no extra packages. See [Subscription only](#2-subscription-only-no-api-billing).

---

## 1. Setup (2 minutes)

You need:
- **Claude Code**, logged in with your Claude account: run `claude`, then `/login`. Keep it updated with `claude update`. The Free plan does not include Claude Code.
- **Python 3.8+**. On Windows, use `python` or `py` where this guide says `python3`.

```bash
git clone <this repo> AgentOrchestration
cd AgentOrchestration
python3 install.py     # optional: makes /refine work in ALL your projects
```

---

## 2. Subscription only (no API billing)

Both modes run through Claude Code on your subscription login. Nothing calls the API with a key.

| Where | Works on subscription? |
|---|---|
| `chat.py` (it runs the `claude` CLI for you) | Yes |
| `/refine` in the `claude` CLI | Yes |
| `/refine` in the **Claude Desktop app → Code tab** or the **VS Code extension** | Yes. They load the same `~/.claude` skills and agents after `install.py`. |
| Regular Claude **Chat** (claude.ai or the Desktop Chat tab) | No. Chat has no subagents. |

**One trap:** if `ANTHROPIC_API_KEY` is set on your computer, `claude -p` (what `chat.py` runs) **always uses the key** and bills per request. It doesn't ask. `chat.py` blocks this by default with `"subscription_only": true`:
- It removes `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` and cloud-provider switches from the calls it makes.
- Before the first call, it runs `claude auth status`. If the login is not your Claude account (for example a key in `~/.claude/settings.json` or an `apiKeyHelper`), it stops and tells you what to remove.

**Check it yourself:** in `claude`, type `/status`. **Login** should show your Claude account, not "API key". This matters for `/refine` too.

**Usage limits:** the loop uses your plan's 5-hour and weekly limits like any other Claude Code use. One answer = **2N + 1 calls** (5 with the default 2 rounds). See [Tips](#8-usage-and-tips).

---

## 3. Two ways to use it

| | **A. Chat script** (`chat.py`) | **B. Inside Claude Code** (`/refine`) |
|---|---|---|
| Best for | Questions, writing, research, plans | Coding work inside a project |
| Review loop | Every message, always | Only messages that start with `/refine` |
| Loop control | Code runs exactly N rounds. Guaranteed. | Claude follows the instructions in the skill |
| Can edit files | No (read-only tools) | Yes (normal Claude Code permissions) |

### A. Chat script: always-on loop

Run it from the folder you want Claude to be able to read (your project, or anywhere):

```bash
python3 /path/to/AgentOrchestration/chat.py            # chat, 2 rounds per answer
python3 /path/to/AgentOrchestration/chat.py -r 3       # 3 rounds per answer
python3 /path/to/AgentOrchestration/chat.py --steps    # also show every draft and review
python3 /path/to/AgentOrchestration/chat.py "question" # one answer, then exit
cat prompt.txt | python3 chat.py -                     # prompt from a file or pipe
```

Inside the chat:

| Command | What it does |
|---|---|
| `/rounds 3` | Set the rounds for the next answers. `0` turns review off. |
| `/steps` | Show or hide the drafts and reviewer feedback |
| `/early` | Stop a loop early when the reviewer says APPROVE |
| `/new` | Start a fresh conversation |
| `"""` | Start or end a multi-line message (for pasting) |
| `/exit` | Quit. It prints `claude --resume <id>` so you can continue in Claude Code. |

Each answer ends with a stats line, for example `[2 revision(s) - 5 Claude calls - 26s]`.
Full transcripts (drafts, reviews, final answers) are saved in `logs/`.

### B. Inside Claude Code: `/refine`

Start `claude` in this folder, or in any folder if you ran `install.py`:

```
/refine how should I structure auth in this Next.js app?
/refine 3 review my plan in PLAN.md and fix the weak parts
```

Claude drafts the answer. It calls the `reviewer` subagent with the draft, applies the fixes, and repeats. Then it prints the final answer and a short "Review log".

---

## 4. Change the number of loops

| Where | How |
|---|---|
| Chat, permanent default | `config.json` → `"rounds": 2` |
| Chat, one session | `python3 chat.py -r 4` |
| Chat, mid-conversation | `/rounds 4` |
| `/refine`, one request | `/refine 4 <request>` |
| `/refine`, default | Edit the `Default rounds: 2` line in `.claude/skills/refine/SKILL.md`, then re-run `install.py` |

---

## 5. Config (`config.json`, chat script only)

| Key | Default | Meaning |
|---|---|---|
| `subscription_only` | `true` | Never bill per API request. Ignores API-key env vars and checks the login before starting. |
| `rounds` | `2` | Review → revise rounds per answer |
| `stop_early` | `false` | Stop when the reviewer says `APPROVE` (saves time and usage) |
| `show_steps` | `false` | Print drafts and reviews, not just the final answer |
| `main_model` | `null` | For example `"opus"` or `"sonnet"`. `null` = your Claude Code default |
| `reviewer_model` | `null` | Same options as `main_model` |
| `main_tools` | `Read,Grep,Glob,WebSearch,WebFetch` | Tools the main agent may use. `""` = none (pure chat). |
| `reviewer_tools` | same | Tools the reviewer may use to check facts |
| `history_turns` | `3` | How many past exchanges the reviewer sees for follow-up questions |
| `log_dir` | `"logs"` | Folder for transcripts. `null` = no logs |
| `timeout_seconds` | `600` | Max time for one Claude call |

---

## 6. Customize the agents

| File | Controls |
|---|---|
| `.claude/agents/reviewer.md` | **Reviewer** instructions and output format. Used by **both** the chat script and `/refine`. |
| `prompts/main.md` | Extra system instructions for the main agent (chat script) |
| `prompts/review.md` | Message sent to the reviewer: request, draft, history |
| `prompts/revise.md` | Message that hands the feedback back to the main agent |
| `.claude/skills/refine/SKILL.md` | The `/refine` loop steps |

Examples: make the reviewer a "security auditor" or a "Canadian tax expert". Make it more or less strict. Change the output format. Placeholders like `{draft}` are filled in by `chat.py`.
After editing the reviewer or the skill, run `python3 install.py` again to update the global copy.

---

## 7. How it works (chat script)

- **Main agent** = one persistent Claude Code session (`--session-id`, then `--resume`). It remembers the whole chat.
- **Reviewer** = a brand-new Claude call every round (`--no-session-persistence`). It is truly independent and never sees earlier reviews. It gets the request, the current draft, and the last few exchanges for context.
- Progress goes to stderr. Final answers go to stdout, so `python3 chat.py "q" > answer.md` works.

---

## 8. Usage and tips

- One answer = 1 draft + N reviews + N revisions = **2N + 1 calls**. With the default of 2, that is 5 calls. It uses about 3–5× the plan usage and time of a normal answer.
- Turn on `stop_early` (or `/early`). Without it, an approved answer is still sent back for another rewrite, which wastes usage.
- On Pro you will hit the 5-hour limit sooner. Set `"main_model": "sonnet"` and `"reviewer_model": "sonnet"` to stretch it, since Opus uses limits faster.
- For quick questions, use `/rounds 0` or plain `claude`. The loop pays off on answers where mistakes cost you: plans, code, research, emails.

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `Claude Code CLI not found` | Install Claude Code and make sure `claude` works in the same terminal |
| `unknown option ...` | Your Claude Code is too old: `claude update` |
| `Not logged in` | Run `claude`, type `/login`, and sign in with your Claude account |
| `...bill per API request...` | Remove the key or helper it names, restart the terminal, and check `/status` |
| `Ignoring ANTHROPIC_API_KEY...` | Just a notice. Calls use your subscription. Remove the variable to silence it. |
| Usage-limit error | You hit your plan's limit. Wait for the reset, or use fewer rounds or `stop_early` |
| `/refine` not found | Run `claude` from this folder, or run `python3 install.py` |
| A call times out | Raise `timeout_seconds` in `config.json` |
| Windows: odd characters | Use Windows Terminal (UTF-8) |
