# Selling the Refine Loop

## The hard truth first

**You cannot hide the source.** The product is three markdown files. Claude Code on the buyer's computer must read them as plain text, so the buyer can too (`~/.claude/plugins/cache/...`). Compiling, obfuscating or zipping changes nothing. Anyone can also rebuild the idea from Anthropic's public docs in an hour.

So the business is not secrecy. It is: a **finished, installed, tested** thing, a **demo that proves it**, **updates** when Claude Code changes, and **domain packs** (security reviewer, legal reviewer, marketing-copy reviewer...). That is how every paid prompt product works.

## What the buyer gets

One file: `dist/refine-loop-<version>.zip`, built by `python package.py`. It is a standard Claude Code plugin.

| Buyer does | Result |
|---|---|
| `claude --plugin-dir refine-loop-1.0.0.zip` | Works for that session. 10-second trial. |
| `claude plugin marketplace add <your-repo>` then `claude plugin install refine-loop@refine-loop-market` | Installed for good. `claude plugin marketplace update` pulls your updates. |
| `/refine <request>` or `/refine -r 3 <request>` | One reviewed answer |
| `claude --agent refine-loop:refiner` | Every answer reviewed |

No Python, no API key. Runs on their own Claude subscription.

## Three ways to distribute

| | How | Pros | Cons |
|---|---|---|---|
| **1. Store download (recommended to start)** | Sell the zip on **Lemon Squeezy** or **Gumroad**. Buyer gets a download link and a PDF/README. | Live in a day. Both are *merchant of record*: they collect HST/GST and foreign VAT for you, which matters for an Ontario seller. Lemon Squeezy also issues license keys. | No auto-updates unless you email a new zip. Source is visible (always true). |
| **2. Private GitHub repo as marketplace** | After purchase, invite the buyer as a read-only collaborator (or to a GitHub org team). They run the two `claude plugin` commands above. | Updates flow with `claude plugin marketplace update`. Feels like a real product. | Manual invites. Fine up to ~100 buyers, then automate with the GitHub API. Buyer needs `gh auth login` or SSH set up. |
| **3. Hosted reviewer (SaaS)** | You run an MCP server; the reviewer step calls your server, which runs the review with **your** API key. | The only way to keep the reviewer prompt private. Recurring revenue. | You pay per review. You need servers, uptime, abuse controls. Contradicts the "no API" promise. Not for v1. |

Start with **1**, offer **2** to buyers who want updates, consider **3** only if you get real traction.

## Pricing reality

- Comparable prompt packs and Claude Code plugins sell for **$19-49 one-time**. A **$5-9/month** tier works only if you keep shipping packs and updates.
- Do not price on "AI pipeline" language. Price on the outcome: "fewer wrong answers, in your own Claude Code, no API bill".
- Anthropic can ship this natively any time. Move fast, keep it cheap, build the audience.

## The marketing demo

`python demo/compare.py "<prompt>"` runs the same prompt through plain Claude Code and through the loop, then writes a side-by-side `.md` and `.html` to `demo/out/`, including what the reviewer caught. See `demo/examples/`.

What the first run showed: on an easy prompt the difference is **small**. Both answers were correct. The loop's win was that it respected "exactly 5 tests" and caught one edge case (`str.upper()` turning `ſ` into `S`). That is honest but not a headline.

To get headline demos, use prompts where plain Claude usually slips:
- Multi-constraint requests ("exactly 5", "under 100 words", "no external libraries")
- Facts with local specifics (Ontario rules, dates, prices, tax)
- Code with edge cases (dates, time zones, unicode, money)
- Ambiguous asks, where the reviewer forces stated assumptions
- Long documents, where consistency breaks down

Run 10 prompts, keep the 3 clearest wins, and show one honest draw. Buyers trust that more than five perfect wins.

## Do before launch

1. Put your name in `package.py` (`author`) and `.claude-plugin/marketplace.json` (`owner`).
2. Add a `LICENSE.md` (one buyer, personal or company use, no resale). `package.py` includes it in the zip when it exists.
3. Run `python package.py`, test the zip with `claude --plugin-dir`, upload it.
4. Record one 60-second screen capture of `demo/compare.py` running.
5. Write the store page around the demo, not the mechanism.

## Risks

- **Copying:** certain. Compete on updates, packs and support, not on secrecy.
- **Claude Code changes:** plugin format, agent names or flags can change. Budget an hour a month to re-test and re-ship.
- **Usage limits:** each answer uses 2N+1 calls of the buyer's plan. Say so on the store page. Default stays at 2 rounds; `-r 1` is the cheap setting.
- **Refunds:** keep them easy. The zip is 3 KB; fighting over it costs more than it earns.
