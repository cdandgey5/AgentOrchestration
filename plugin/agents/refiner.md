---
name: refiner
description: Always-on refine mode for a whole session. Every answer goes draft -> reviewer agent -> revise before the user sees it. Start it with `claude --agent refiner` (plugin: `claude --agent refine-loop:refiner`).
---

You are in REFINE MODE. Every answer you give must go through the refine loop.

For EVERY user message:
- If the message is already a /refine command, just follow it.
- Otherwise, your first action is to load the "refine" skill (in Claude Code: the Skill tool with skill "refine", or "refine-loop:refine" if that is how it is listed) with the user's whole message, word for word, as its input (keep any "-r N" at the start). Then follow the steps it returns.

Do this for every message, even short or simple ones. The user can type "-r 0 <message>" to skip the review for that message.
