# Refine Loop 1.1.0

Every answer goes draft -> independent reviewer agent -> revise before you see it.
Works in Claude Code and GitHub Copilot. Five text files, no code. MIT license.

## Claude Code
- Try once:    `claude --plugin-dir refine-loop-1.1.0.zip`
- Install:     `claude plugin marketplace add cdandgey5/AgentOrchestration`
               `claude plugin install refine-loop@refine-loop-market`
- One message: `/refine <request>`   rounds: `/refine -r 3 <request>` (`-r 0` = no review)
- Session:     `claude --agent refine-loop:refiner`
- Remove:      `claude plugin uninstall refine-loop@refine-loop-market`

## GitHub Copilot (CLI, VS Code)
- Install:     `copilot plugin install cdandgey5/AgentOrchestration:plugin`
- One message: `Use the /refine skill: <request>`
- Session:     `copilot --agent refiner`   (VS Code: pick "refiner" in the agents dropdown)
- Remove:      `copilot plugin uninstall refine-loop`

## Settings
- Default rounds, stop-early: `skills/refine/SKILL.md`, the "Settings" lines
- What the reviewer checks:   `agents/reviewer.md` (Claude) and `com.github.copilot/agents/reviewer.agent.md` (Copilot)

Security notes: https://github.com/cdandgey5/AgentOrchestration/blob/main/SECURITY.md
