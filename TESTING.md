# Test the plugin

A plugin is a folder (or a zip of it) with agents and skills inside. Claude Code or Copilot loads it, and you get a `/refine` skill, a `reviewer` agent and a `refiner` agent. No code runs.

Do the tests in order. Each one says what you should see. Write down anything that differs, with the exact prompt you used.

---

## Claude Code

### 0. Before you start
```
claude --version        # need 2.1.224 or newer; else: claude update
```

### 1. Zip, one session (2 min). Installs nothing.
1. Download `releases/refine-loop-1.1.0.zip`. Do **not** unzip it.
2. From the folder that holds it:
   ```
   claude --plugin-dir refine-loop-1.1.0.zip
   ```
3. Type `/` and check the list for **refine** (may show as `refine-loop:refine`).
4. Run: `/refine -r 1 Give me 3 tips to save on winter heating in Ontario. One line each.`
5. **Expect:** 20-40 s of work, one line `Round 1/1: reviewer said ..., N issues, fixed N.`, the answer, then a short `Review log`. No "Draft:" text before the answer.
6. `/agents` should list `refine-loop:reviewer` and `refine-loop:refiner`. `/exit`.

### 2. Whole-session mode (3 min)
```
claude --plugin-dir refine-loop-1.1.0.zip --agent refine-loop:refiner
```
Ask a normal question. **Expect:** `Round 1/2` and `Round 2/2` lines, then the answer. `-r 0 hi` answers at once with no review.

### 3. Install for good (5 min)
Needs Git access to GitHub from your terminal (`gh auth login`, or SSH).
```
claude plugin marketplace add cdandgey5/AgentOrchestration
claude plugin install refine-loop@refine-loop-market
claude plugin list
```
**Expect:** `refine-loop@refine-loop-market`, `Version: 1.1.0`, `Status: enabled`. Now `/refine` works in every folder, in the terminal, the Desktop app's Code tab and VS Code.
Files live in `~/.claude/plugins/cache/refine-loop-market/refine-loop/1.1.0/` (Windows: `C:\Users\<you>\.claude\plugins\...`). Open the folder: plain text files.

Whole-session mode in the Desktop app (no flags there): add `"agent": "refine-loop:refiner"` to `~/.claude/settings.json`. Remove the line to turn it off.

### 4. Remove (1 min)
```
claude plugin uninstall refine-loop@refine-loop-market
claude plugin marketplace remove refine-loop-market
claude plugin list
```
**Expect:** no `refine-loop`. The cache folder gets an `.orphaned_at` marker and is deleted about 14 days later; delete it by hand if you want it gone now.

---

## GitHub Copilot (not tested by the author yet: you are first)

### 5. Before you start
Copilot CLI installed and signed in (`copilot` opens a session; `/login` if asked). Check `copilot --version`. Plugins need a recent CLI; run `copilot update` if a command below is unknown.

### 6. Install (2 min)
```
copilot plugin install cdandgey5/AgentOrchestration:plugin
copilot plugin list
```
**Expect:** `refine-loop` listed as installed. Files live in `~/.copilot/installed-plugins/_direct/...`.
Alternative (via marketplace): `copilot plugin marketplace add cdandgey5/AgentOrchestration` then `copilot plugin install refine-loop@refine-loop-market`.

### 7. One message (3 min)
Start `copilot` in any folder and type:
```
Use the /refine skill: -r 1 Give me 3 tips to save on winter heating in Ontario. One line each.
```
**Expect:** Copilot loads the skill, delegates to the `reviewer` custom agent (you should see a subagent/task running), prints `Round 1/1: ...`, then the answer and a `Review log`.
Also try `/skills list` (should show `refine`) and `/agent` (should list `reviewer` and `refiner`).

### 8. Whole-session mode (3 min)
```
copilot --agent refiner
```
Ask a normal question. **Expect:** `Round 1/2`, `Round 2/2`, then the answer. In VS Code: pick **refiner** in the chat agents dropdown and ask the same.

### 9. Remove
```
copilot plugin uninstall refine-loop
copilot plugin list
```

### What to report for Copilot
- Did the skill load when you wrote `/refine`? If not, did "Use the refine skill" work?
- Did the reviewer run as a separate agent (a subagent/task appeared)? If Copilot answered inline without delegating, say so.
- Exact text of any error.

---

## What good and bad look like (both tools)

| Check | Good | Bad |
|---|---|---|
| Speed | 20-40 s with `-r 1`, 40-80 s with 2 rounds | Over 2 min: reviewer is web-searching a lot. Lower rounds or remove `web` from the reviewer's tools. |
| Status lines | One `Round i/N` line per round | Draft printed before the final answer, or no status lines |
| Reviewer quality | Specific issues, each with a fix | "No change needed" items listed as issues |
| Final answer | Never mentions reviewer, draft or revision | The answer talks about the review process |

## Rebuild after a change
Edit `.claude/agents/*.md` or `.claude/skills/refine/SKILL.md` (the single source; Copilot's `*.agent.md` files are generated), bump `VERSION` in `package.py`, then:
```
python package.py
```
Commit `plugin/` and `releases/`. Users update with `claude plugin marketplace update` + `claude plugin update refine-loop@refine-loop-market`, or `copilot plugin update refine-loop`.
