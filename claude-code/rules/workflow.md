# How to work on a task

## Reading markdown

Do not read `.md` files on your own initiative. Docs go stale, and a wrong README costs more than no README - the code is the source of truth.

Read a markdown file only when:
- I named it, or my request clearly points at it ("check the readme", "follow the migration guide")
- it is `CLAUDE.md`, a file under `.claude/`, or a `SKILL.md` you were told to use
- a `CLAUDE.md` links to it or names it, and the task in front of you needs it. Needs means you cannot finish the task correctly without it - not that it looks interesting, not to "get some context first". Read it when you hit the point where it matters, not upfront
- you asked me first and I said yes

Same for `docs/` folders and wikis: name what you would like to read and why, in one line, then wait.

## Before you say you are done

Two steps, every task that changed files. Run them before the final message, not after.

**1. Review your own diff.** Read what you actually changed (`git diff HEAD`, plus `git status --short` for new files) and look for:
- code that got longer than it needed to be - a helper used once, a variable that only forwards a value, a layer that adds no behaviour
- leftovers: debug output, commented-out attempts, unused imports/params, dead branches
- duplication you introduced, or something that already exists in the codebase and you rebuilt
- scope creep: changes the task did not ask for
- comments that violate the comment rules

Apply what is safe and behaviour-preserving. Report in two or three lines what you cleaned up, and name anything you deliberately left alone.

**2. Ask about docs.** If the task did not already tell you which docs to update, ask - do not update anything on your own. Name the concrete candidates you found and let me pick:

> Docs: `README.md` (section "Setup") and `docs/api.md` mention the changed endpoint. Update both, one, or neither?

If the task named the docs, just do it and skip the question. If nothing in the repo references what changed, say "no doc touches this" in one line instead of asking.
