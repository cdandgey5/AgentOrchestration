# Security

## What this is

Five Markdown and JSON text files. **No code runs.** Claude Code or GitHub Copilot reads the files as instructions for the model. There is no installer, no binary, no script, no dependency, no network call made by the plugin itself.

You can verify this in two minutes: open the `plugin/` folder (or `~/.claude/plugins/cache/...` / `~/.copilot/installed-plugins/...` after install) and read every file. In Claude Code, `claude plugin details refine-loop@refine-loop-market` prints the component list and its context cost.

## Where your data goes

**This is not offline.** Claude Code and Copilot send your prompts and files to Anthropic or GitHub to run the model. That is true with or without this plugin. The plugin adds **no new destination**: the reviewer is a second call to the same provider, under the same account and policy.

What changes: each answer makes **2N+1 model calls** instead of 1 (5 with the default 2 rounds). Your draft is sent again to the reviewer. If your company's AI policy allows Claude Code or Copilot on a project, this plugin stays within that policy. If it does not, this plugin does not change that.

## What each agent can do

| Component | Tools | Can it change files or run commands? |
|---|---|---|
| `reviewer` agent | Read, Grep, Glob, WebSearch, WebFetch (Copilot: read, search, web) | **No.** It only reads and returns text. |
| `refiner` agent (whole-session mode) | The same tools Claude Code or Copilot normally give the main agent | Yes, like any normal session. Your usual permission prompts still apply. |
| `/refine` skill | None of its own. It is instructions for the current session's agent. | Same as the current session |

The plugin ships **no hooks, no MCP servers, no settings changes, no pre-approved permissions**.

## Known risks

1. **Prompt injection through the reviewer.** The reviewer can read files and web pages. A malicious page or file could try to plant "fix this" instructions in its review. Mitigation: the reviewer cannot act on anything itself, and the skill tells the main agent to treat the review as advice about the draft only, never as instructions to run commands or change other files. Residual risk: the same as any session where the model reads untrusted content. Restrict `WebFetch`/`web` in `agents/reviewer.md` if your work is sensitive.
2. **Usage.** 3-5x the tokens of a normal answer. On shared company seats this is real money or faster rate limits. Default stays at 2 rounds; `-r 1` or `stop early: yes` cuts it.
3. **Model trust.** The reviewer is the same kind of model as the author. It catches many mistakes, not all. Do not treat an approved answer as verified.

## What is NOT provided

There is no security certification for Claude Code or Copilot plugins, from Anthropic, GitHub, or anyone else. Nothing here is audited or certified. What you get instead is a plugin small enough to read in full before you use it.

## Verify a download

Release zips come with `SHA256SUMS`. Check before use:

```
# Windows PowerShell
Get-FileHash releases\refine-loop-1.1.0.zip -Algorithm SHA256
# Mac / Linux
shasum -a 256 releases/refine-loop-1.1.0.zip
```

Compare with the line in `releases/SHA256SUMS`.

## Reporting

- Something you do not want public: use GitHub's private vulnerability reporting, <https://github.com/cdandgey5/AgentOrchestration/security/advisories/new>. You get a reply within 7 days.
- Anything else: open an issue at <https://github.com/cdandgey5/AgentOrchestration/issues>.

Automated checks: [OpenSSF Scorecard](https://scorecard.dev/viewer/?uri=github.com/cdandgey5/AgentOrchestration) runs weekly; CodeQL scans the Python helpers on every push.
