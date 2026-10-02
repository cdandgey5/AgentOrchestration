---
name: refine
description: Draft -> independent reviewer subagent -> revise loop, then show only the final answer. Use ONLY when the user types /refine or the refiner agent tells you to. Never invoke it on your own.
argument-hint: "[-r rounds] <your request>"
---

# Refine loop

Settings (edit these lines to change the defaults):
- Default rounds: 2
- Stop early when the reviewer says APPROVE: no

User input: $ARGUMENTS

## Steps

1. **Rounds.** If the input starts with `-r N` (example: `-r 3 explain X`), use N rounds and remove `-r N` from the request. Otherwise use the default rounds. `-r 0` means no review: just answer directly.

2. **Draft.** Do the work and write your best complete answer, exactly as you normally would (read files, run searches, use tools as needed). Do NOT show the draft to the user. Keep it for the reviewer.
   - If the request is a change to files: make the changes. The "draft" is a summary of what you changed plus the list of changed files, so the reviewer can read them.

3. **Review loop.** For each round i = 1..N:
   a. Call the Agent tool with `subagent_type: "reviewer"`. The reviewer does NOT see this conversation. Its prompt must contain:
      - `<user_request>`: the user's request, word for word.
      - `<context>`: anything from earlier in this conversation the reviewer needs (key facts, constraints, file paths). Write "none" if nothing.
      - `<draft>`: the complete current draft, word for word. Never summarize it.
      Wait for the reviewer's result before doing anything else.
   b. Read the feedback. Fix every valid issue. Ignore points that are wrong; you own the final answer. Produce the full revised draft (or edit the files again).
   c. Print one status line: `Round i/N: reviewer said <VERDICT>, <k> issues, fixed <x>.`
   d. If stop-early is "yes" and the verdict is APPROVE, stop the loop.

   Every round uses a NEW reviewer call on the latest draft. Run all N rounds even if the request looks simple, unless stop-early applies.

4. **Final answer.** Print the final answer in full. Do not mention drafts in the answer itself. After it, add:

   ```
   ---
   Review log: <up to 3 short bullets on what the reviews changed>
   ```
