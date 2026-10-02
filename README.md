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

It runs on your existing Claude Code login. You need no API key and no extra packages.

---

## 1. Setup (2 minutes)

You need:
- **Claude Code**, installed and logged in. Run `claude` once to check. Keep it updated with `claude update`.
- **Python 3.8+**. On Windows, use `python` or `py` where this guide says `python3`.

```bash
git clone <this repo> AgentOrchestration
cd AgentOrchestration
python3 install.py     # optional: makes /refine work in ALL your projects
```

---

## 2. Two ways to use it

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

Each answer ends with a stats line, for example `[2 revision(s) - 26s - est. $0.10]`.
Full transcripts (drafts, reviews, final answers) are saved in `logs/`.

### B. Inside Claude Code: `/refine`

Start `claude` in this folder, or in any folder if you ran `install.py`:

```
/refine how should I structure auth in this Next.js app?
/refine 3 review my plan in PLAN.md and fix the weak parts
```

Claude drafts the answer. It calls the `reviewer` subagent with the draft, applies the fixes, and repeats. Then it prints the final answer and a short "Review log".

---

## 3. Change the number of loops

| Where | How |
|---|---|
| Chat, permanent default | `config.json` → `"rounds": 2` |
| Chat, one session | `python3 chat.py -r 4` |
| Chat, mid-conversation | `/rounds 4` |
| `/refine`, one request | `/refine 4 <request>` |
| `/refine`, default | Edit the `Default rounds: 2` line in `.claude/skills/refine/SKILL.md`, then re-run `install.py` |

---

## 4. Config (`config.json`, chat script only)

| Key | Default | Meaning |
|---|---|---|
| `rounds` | `2` | Review → revise rounds per answer |
| `stop_early` | `false` | Stop when the reviewer says `APPROVE` (saves time and money) |
| `show_steps` | `false` | Print drafts and reviews, not just the final answer |
| `main_model` | `null` | For example `"opus"` or `"sonnet"`. `null` = your Claude Code default |
| `reviewer_model` | `null` | Same options as `main_model` |
| `main_tools` | `Read,Grep,Glob,WebSearch,WebFetch` | Tools the main agent may use. `""` = none (pure chat). |
| `reviewer_tools` | same | Tools the reviewer may use to check facts |
| `history_turns` | `3` | How many past exchanges the reviewer sees for follow-up questions |
| `log_dir` | `"logs"` | Folder for transcripts. `null` = no logs |
| `timeout_seconds` | `600` | Max time for one Claude call |

---

## 5. Customize the agents

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

## 6. How it works (chat script)

- **Main agent** = one persistent Claude Code session (`--session-id`, then `--resume`). It remembers the whole chat.
- **Reviewer** = a brand-new Claude call every round (`--no-session-persistence`). It is truly independent and never sees earlier reviews. It gets the request, the current draft, and the last few exchanges for context.
- Progress goes to stderr. Final answers go to stdout, so `python3 chat.py "q" > answer.md` works.

---

## 7. Costs and tips

- One answer = 1 draft + N reviews + N revisions = **2N + 1 calls**. With the default of 2, that is 5 calls, about 3–5× the cost and time of a normal answer.
- Turn on `stop_early` (or `/early`). Without it, an approved answer is still sent back for another rewrite.
- Use a strong reviewer and a cheaper main agent, or the reverse. Set this with `main_model` / `reviewer_model`.
- For quick questions, use `/rounds 0` or plain `claude`. The loop pays off on answers where mistakes cost you: plans, code, research, emails.

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `Claude Code CLI not found` | Install Claude Code and make sure `claude` works in the same terminal |
| `unknown option ...` | Your Claude Code is too old: `claude update` |
| Not logged in / auth error | Run `claude` once and log in |
| `/refine` not found | Run `claude` from this folder, or run `python3 install.py` |
| A call times out | Raise `timeout_seconds` in `config.json` |
| Windows: odd characters | Use Windows Terminal (UTF-8) |
