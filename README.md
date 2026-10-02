# Refine Loop for Claude Code

Every answer is checked by a reviewer before you see it.
**Main agent drafts → reviewer subagent critiques → main agent revises.** This repeats N times (default **2**). Then you get the final answer.

```
your message
   │
   ▼
Main agent ── draft ──► Reviewer subagent (fresh context, every round)
   ▲                         │
   └──── feedback ◄──────────┘     repeat N times (default 2)
   │
   ▼
final answer
```

It runs on your **Claude subscription** (Pro, Max, Team or Enterprise) through Claude Code. There are **no API requests and no API key**.

---

## 1. What you need

| Thing | Needed? |
|---|---|
| Claude Pro / Max / Team / Enterprise plan | **Yes**. The Free plan has no Claude Code. |
| **Claude Desktop app** (GUI) **or** Claude Code **CLI** (terminal) | **One of them** |
| Python | **No.** Only for the optional `chat.py` script ([option C](#c-chatpy-script-needs-python)). |
| Git | **No.** Download the ZIP instead. |

**Get Claude:**
- **Desktop app (GUI):** download from <https://claude.ai/download> and sign in.
- **CLI (terminal):**
  - Windows (PowerShell): `irm https://claude.ai/install.ps1 | iex`
  - Mac: `curl -fsSL https://claude.ai/install.sh | bash`

  Then run `claude` and sign in with your Claude account.

**Get this framework:** on GitHub click **Code → Download ZIP**, then unzip it, for example to `Documents\AgentOrchestration`. Or use `git clone`.

---

## 2. Run it

### A. Desktop app (GUI): no Python, every message reviewed

1. Open the Claude Desktop app and click the **Code** tab.
2. Choose **Local**, click **Select folder**, and pick the `AgentOrchestration` folder.
3. Type your message as normal. Every answer goes through the review loop.

This works because the folder's `.claude/settings.json` turns on **refine mode** (`"agent": "refiner"`).
If your app version ignores that setting, type `/refine <your message>` instead. It does the same thing for one message.

### B. CLI (terminal): no Python

```bash
cd path/to/AgentOrchestration
claude                     # every message is reviewed in this folder
```

To use it in **other projects**, do the [global install](#4-use-it-in-all-your-projects) once. Then:

```bash
claude --agent refiner     # every message is reviewed, in any folder
claude                     # normal Claude; type /refine <msg> when you want a review
```

### C. `chat.py` script: needs Python

The loop runs in code, so it always does exactly N rounds. It is good for Q&A and research. Python 3.8+:
- **Windows:** `winget install Python.Python.3.12` (or python.org, and tick **"Add python.exe to PATH"**). Reopen the terminal and check with `python --version`.
- **Mac:** run `python3 --version`. If it is missing, run `xcode-select --install`.

```bash
python3 chat.py              # chat (Windows: python chat.py)
python3 chat.py -r 3         # 3 rounds per answer
python3 chat.py --steps      # also show every draft and review
python3 chat.py "question"   # one answer, then exit
```

Inside the chat: `/rounds 3`, `/steps`, `/early`, `/new`, `/help`, `/exit`. Use `"""` to start and end a multi-line paste.
Full transcripts are saved in `logs/`.

---

## 3. Where to set parameters

| What | Desktop app / CLI (refine mode, `/refine`) | `chat.py` |
|---|---|---|
| **Rounds, default** | `Default rounds: 2` line in `.claude/skills/refine/SKILL.md` | `"rounds"` in `config.json` |
| **Rounds, one message** | Start the message with `-r 3` (`-r 0` = no review) | Same: `-r 3 your message` |
| **Rounds, one session** | - | `python3 chat.py -r 3` or `/rounds 3` |
| **Stop when reviewer approves** | `Stop early ...: no` → `yes` in `SKILL.md` | `"stop_early": true` or `/early` |
| **Main model** | Desktop: model menu next to Send. CLI: `/model sonnet` | `"main_model": "sonnet"` |
| **Reviewer model** | `model: inherit` → `model: opus` in `.claude/agents/reviewer.md` | `"reviewer_model": "opus"` |
| **What the reviewer checks** | `.claude/agents/reviewer.md` | Same file |
| **Turn refine mode off** | Delete `.claude/settings.json` in this folder | - |

After editing a file, **repeat the global install** (if you did it) so the copy in `~/.claude` matches.

---

## 4. Use it in all your projects

This copies the reviewer, the refine-mode agent and `/refine` to `~/.claude`, where every project can find them.

**Windows (PowerShell), run inside the AgentOrchestration folder:**
```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\agents", "$HOME\.claude\skills" | Out-Null
Copy-Item .claude\agents\*.md "$HOME\.claude\agents\" -Force
Copy-Item .claude\skills\refine "$HOME\.claude\skills\" -Recurse -Force
```

**Mac / Linux:**
```bash
mkdir -p ~/.claude/agents ~/.claude/skills
cp .claude/agents/*.md ~/.claude/agents/
cp -R .claude/skills/refine ~/.claude/skills/
```

**With Python:** `python3 install.py` does the same, backs up any files it replaces, and `--uninstall` removes them.

---

## 5. Subscription only (no API billing)

- The Desktop app and the CLI use the Claude account you signed in with.
- **Check it:** in Claude Code type `/status`. **Login** should show your Claude account, not "API key".
- **Trap:** if `ANTHROPIC_API_KEY` is set on your computer, `claude -p` (what `chat.py` runs) uses the key and bills per request without asking. `chat.py` blocks this by default (`"subscription_only": true`):
  - it ignores API-key variables;
  - it checks `claude auth status` before the first call and stops if the login is not your Claude account.
- **Usage limits:** one answer = 1 draft + N reviews + N revisions = **2N + 1 calls** (5 with the default). This uses your plan's 5-hour and weekly limits about 3–5× faster than normal chat.

---

## 6. Which way to choose

| | A/B: refine mode | `/refine` in normal Claude | C: `chat.py` |
|---|---|---|---|
| Python | No | No | Yes |
| GUI | Yes | Yes | No (terminal) |
| Every message reviewed | Yes | Only `/refine` messages | Yes |
| Exactly N rounds guaranteed | Claude follows the steps | Claude follows the steps | Yes, enforced in code |
| Best for | Chat, questions, writing, plans | Coding work in a project | Q&A and research with full logs |

Refine mode replaces Claude Code's default coding instructions with the refine loop. For big coding jobs, use normal `claude` with `/refine`.

---

## 7. `config.json` (chat.py only)

| Key | Default | Meaning |
|---|---|---|
| `subscription_only` | `true` | Never bill per API request |
| `rounds` | `2` | Review → revise rounds per answer |
| `stop_early` | `false` | Stop when the reviewer says `APPROVE` (saves time and usage) |
| `show_steps` | `false` | Print drafts and reviews too |
| `main_model` / `reviewer_model` | `null` | `"opus"`, `"sonnet"`, `"haiku"`. `null` = your default |
| `main_tools` / `reviewer_tools` | `Read,Grep,Glob,WebSearch,WebFetch` | Tools each agent may use. `""` = none |
| `history_turns` | `3` | Past exchanges the reviewer sees, for follow-up questions |
| `log_dir` | `"logs"` | Transcript folder. `null` = no logs |
| `timeout_seconds` | `600` | Max time for one Claude call |

---

## 8. Files

| File | What it is |
|---|---|
| `.claude/agents/reviewer.md` | The **reviewer**: what it checks and its reply format. Shared by every mode. |
| `.claude/agents/refiner.md` | **Refine mode**: runs `/refine` on every message |
| `.claude/skills/refine/SKILL.md` | **`/refine`**: the loop steps, default rounds, stop-early |
| `.claude/settings.json` | Turns on refine mode when you open this folder |
| `chat.py`, `config.json`, `prompts/` | The Python chat script and its settings and message templates |
| `install.py` | Optional global install (Python) |

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| Desktop app answers without reviewing | Use `/refine <message>`, or check that you opened the AgentOrchestration folder itself |
| `/refine` not found | Open this folder, or do the [global install](#4-use-it-in-all-your-projects) |
| `python` not found | Install Python ([option C](#c-chatpy-script-needs-python)), or use option A or B, which need no Python |
| `Claude Code CLI not found` (chat.py) | Install the CLI and check that `claude` works in the same terminal |
| `Not logged in` | Run `claude`, type `/login`, and sign in with your Claude account |
| `...bill per API request...` | Remove the key or helper it names, restart the terminal, and check `/status` |
| `unknown option ...` | Update Claude Code: `claude update` |
| Usage-limit error | Wait for the reset. Use fewer rounds, `-r 0` for quick messages, or stop-early. |
