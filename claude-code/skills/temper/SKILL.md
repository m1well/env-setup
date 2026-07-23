---
name: temper
description: Interview the user relentlessly about a plan, design, or decision until reaching a shared understanding — surfacing hidden assumptions first, weighting each decision by reversibility, and logging the outcome at the end. Invoked only via /temper.
disable-model-invocation: true
---

# Temper

Put a plan, design, or decision under heat until only the strong parts survive. Relentless and collaborative — you are hardening my thinking, not agreeing with me.

**Start from** my plan document — `START.md` by convention — if one exists. Look for it in the root directory and one or two levels below; take the first match. Don't ask for a folder name — any folder works, so I can drop the file into a `.gitignore`d subfolder to keep it out of version control. Read the file in full before the first question. No document yet? Have me sketch the plan inline first — temper needs something concrete to attack.

**How to run it**
- One question at a time; wait for my answer before the next. Several at once is bewildering.
- Always give your recommended answer with a one-line why — never a bare question.
- Look up facts yourself (code, docs, tools). The decisions are mine.
- Guard scope: if something smells like gold-plating, ask "do we need this for v1?"

**1. Assumptions first.** Make the plan's implicit assumptions explicit before touching any decision — the real risk hides in what's taken for granted. Probe scale, users, data, constraints, dependencies, and the happy path. Flag any assumption that would invalidate large parts of the plan if wrong, and put the shakiest ones to me one at a time.

**2. Walk the decision tree.** Branch by branch, dependencies before the decisions built on them. Tag each one a two-way door (cheap to undo) or a one-way door (expensive/irreversible) and say the tag out loud so I see where the effort goes. Match the heat: wave two-way doors through with a default; pull one-way doors apart — alternatives, edge cases, failure modes.

**3. Log the outcome.** First ask me whether I want a written log at all — for small tasks the tempering in the console is enough and no file is needed. Only if I say yes, write each significant decision to `DECISIONS.md` — placed in the same folder as `START.md` (or append to the plan doc) — so we don't re-grill it next time: what, why, alternatives rejected, and its door tag. Offer to write the one-way doors up as ADRs.

**In plan mode, the log isn't optional.** Plan-mode writes are blocked until the plan is approved, so a mid-interview `DECISIONS.md` write fails silently and the decisions get swallowed by the plan preview. Instead: shape the plan I hand to `ExitPlanMode` *as* the decision log — same what/why/alternatives/door-tag structure — and make writing it to `DECISIONS.md` the first action once the plan is approved. Approving the plan is my consent to log, so skip the separate ask.

**Done when** the assumptions are confirmed, every open branch is resolved, and the log is either written or explicitly skipped. Confirm that with me explicitly — then, and only then, act.
