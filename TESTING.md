# Test the plugin (15 minutes, no Python)

A Claude Code **plugin** is a folder (or a zip of it) with agents and skills inside. Claude Code loads it, and you get new slash commands and agents. This plugin adds `/refine`, the `reviewer` agent and the `refiner` agent.

Do the tests in order. Each one says what you should see.

## 0. Before you start

Open a terminal (Windows: **PowerShell**. Mac: **Terminal**) and check:

```
claude --version
```

You need **2.1.224 or newer**. If it is older, run `claude update`. If `claude` is not found, install Claude Code (see README section 1), then run `claude` once and sign in.

## Test 1: the zip, one session (2 minutes)

This is what a buyer who downloads the zip from your store will do.

1. Put `refine-loop-1.0.0.zip` in a folder, for example `Downloads`. Do **not** unzip it.
2. In the terminal, go to that folder and start Claude Code with the plugin:
   ```
   cd Downloads
   claude --plugin-dir refine-loop-1.0.0.zip
   ```
3. Type `/` and look at the list. You should see **refine** (it may appear as `refine-loop:refine`).
4. Type this and press Enter:
   ```
   /refine -r 1 Give me 3 tips to save on winter heating in Ontario. One line each.
   ```
5. **You should see:** Claude works for 20-40 seconds, prints one line like `Round 1/1: reviewer said REVISE, 2 issues, fixed 2.`, then the answer, then a short `Review log`.
6. Type `/agents`. You should see `refine-loop:reviewer` and `refine-loop:refiner` in the list.
7. Type `/exit`. The plugin is gone with the session. Nothing was installed.

**If `/refine` is not in the list:** type `/refine-loop:refine` instead. If that is missing too, run `claude plugin --help` to confirm your version supports plugins, and check you ran the command from the folder that holds the zip.

## Test 2: whole-session mode (3 minutes)

Every message gets reviewed, no `/refine` needed:

```
claude --plugin-dir refine-loop-1.0.0.zip --agent refine-loop:refiner
```

Type a normal question, for example `What should I check before buying a used car in Ontario? Keep it short.`

**You should see:** the `Round 1/2` and `Round 2/2` status lines, then the answer. Try `-r 0 hi` and it should answer at once with no review.

## Test 3: install it for good (5 minutes)

This is what a buyer who gets access to your GitHub repo will do. Your repo is the "marketplace".

1. Make sure Git can reach your GitHub account from the terminal. Easiest: install [GitHub CLI](https://cli.github.com) and run `gh auth login`. If you already clone private repos with SSH, you are set.
2. Add the marketplace and install:
   ```
   claude plugin marketplace add cdandgey5/AgentOrchestration
   claude plugin install refine-loop@refine-loop-market
   ```
   **You should see:** `Successfully added marketplace: refine-loop-market` and `Successfully installed plugin: refine-loop@refine-loop-market`.
3. Check it:
   ```
   claude plugin list
   ```
   **You should see:** `refine-loop@refine-loop-market`, `Version: 1.0.0`, `Status: enabled`.
4. Start Claude Code **in any folder**, with no flags, and run `/refine -r 1 <any question>`. It works everywhere now.
5. Later, after you push a new version: `claude plugin marketplace update` then `claude plugin update refine-loop@refine-loop-market`.

**Where it lives on your disk:** `~/.claude/plugins/cache/refine-loop-market/refine-loop/1.0.0/` (Windows: `C:\Users\<you>\.claude\plugins\...`). Open it. You will see the plain markdown files. This is why the source cannot be hidden.

## Test 4: remove it (1 minute)

```
claude plugin uninstall refine-loop@refine-loop-market
claude plugin marketplace remove refine-loop-market
claude plugin list
```

**You should see:** no `refine-loop` in the list. `/refine` is gone from new sessions.

## Test 5: in the Claude Desktop app (optional)

The Desktop app's **Code** tab uses the same plugin install. After Test 3, open any folder in the Code tab and type `/refine -r 1 <question>`. It should behave like Test 1.

## What to look at while testing

| Check | Good sign | Bad sign |
|---|---|---|
| Speed | 20-40 s with `-r 1`, 40-80 s with the default 2 rounds | Over 2 minutes: the reviewer is probably using web search a lot. Lower rounds or restrict tools in `agents/reviewer.md`. |
| Status lines | Exactly one `Round i/N` line per round | The draft printed before the final answer, or no status lines |
| Reviewer quality | Specific issues with a fix each | "No change needed" items listed as issues |
| Final answer | No mention of "reviewer", "draft" or "revision" inside the answer | The answer talks about the review process |

Write down anything in the "bad sign" column with the exact prompt you used. That is the fix list for version 1.0.1.

## Rebuild the zip after a change

Edit `.claude/agents/reviewer.md` or `.claude/skills/refine/SKILL.md`, then:

```
python package.py
```

This refreshes `plugin/` and writes `releases/refine-loop-<version>.zip`. Bump `VERSION` in `package.py` first so buyers' `claude plugin update` sees the new version. Commit and push.
