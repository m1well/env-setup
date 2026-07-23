---
name: next-tidy
description: Stages all changes (git add -A), then reads the diff and suggests the single smallest next tidy toward cleaner code — one safe, behavior-preserving step, no rewrites, no new abstractions. Invoked via /next-tidy.
disable-model-invocation: true
argument-hint: [file or path — optional, to narrow the suggestion]
---

# Next Tidy

Give me the *next small step* toward cleaner code — in the spirit of Kent Beck's *Tidy First?*. One tidy, not a plan. Small enough to do in a couple of minutes, safe enough to need no new tests, and it must not change behavior.

**Look at** all current changes. First stage everything with `git add -A` so nothing is missed, then read the staged diff: `git diff --cached` (plus `git diff --cached --stat` for the overview; new files show up as additions — read them in full). If `$ARGUMENTS` names a file or path, narrow the suggestion to that. Working tree already clean (nothing to stage)? Say so — don't invent work.

**Pick exactly one.** Scan the staged diff, find every candidate, then surface the single highest-leverage *smallest* tidy — the one that buys the most readability for the least risk. Not a list. If the diff is already clean, say so plainly instead of inventing work.

**What counts as a tidy** (behavior stays identical):
- Guard clause / early return to flatten nesting
- Extract a well-named helper or function from a dense block
- Rename a variable/function that misleads or under-explains
- Delete dead code, commented-out code, or an unused import/param
- Inline a needless variable, or add an explaining variable for a cryptic expression
- Replace a magic value with a named constant
- Normalize symmetry — make parallel things read in parallel
- Reorder for reading order / move a declaration next to its first use
- Simplify a boolean or collapse a redundant conditional

**What to avoid** — this is where it goes wrong:
- No behavior change, no bug fixes, no API changes. A tidy that needs a new test isn't a tidy.
- No new layer, interface, or abstraction "for later" — premature abstraction is worse than the duplication it hides. Two occurrences are not a pattern.
- Nothing that spreads across many files or touches code outside the staged diff.
- Nothing that takes more than a few minutes. If it's big, it's not the *next* step.

**Answer with:**

- **The tidy** — one short title (e.g. "Guard clause for the null branch")
- **Where** — `file:line`
- **Before → After** — a minimal snippet, just the lines that move
- **Why** — 1–2 lines: what it buys (readability, testability, less nesting) and why it's safe
- **Other candidates** *(optional)* — only if more exist: one-line headlines, no detail, so I see the backlog without losing the single next step

Then offer to apply it if I want — but suggest first, don't touch the code unasked.
