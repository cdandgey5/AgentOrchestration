# Refine Loop 1.0.0

Every answer goes draft -> independent reviewer -> revise before you see it.

## Use it
- One message:      type `/refine <your request>` in Claude Code
- Rounds:           `/refine -r 3 <request>` (`-r 0` = no review). Default is 2.
- Whole session:    `claude --agent refiner`

## Install
- Try it once:      `claude --plugin-dir refine-loop.zip`
- Keep it:          `claude plugin marketplace add <marketplace you were given>`
                    `claude plugin install refine-loop@<marketplace>`

## Settings
- Default rounds and stop-early: `skills/refine/SKILL.md`, the "Settings" lines
- What the reviewer checks:      `agents/reviewer.md`
