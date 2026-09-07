---
name: mw-wrapup
description: Closes out a task - reviews everything changed since the last commit, applies the safe cleanups, then asks which docs need updating. The manual version of the automatic end-of-task check. Invoked via /mw-wrapup.
disable-model-invocation: true
argument-hint: [file or path - optional, to narrow the review]
---

# Wrap up

Close out what we just built. Two passes, in this order, then stop.

Narrow to `$ARGUMENTS` if it names a file or path, otherwise take everything that changed.

## 1. Shrink the diff

Read the actual changes - `git diff HEAD` and `git status --short` for new files, read new files in full. Then go through them looking for code that can go away:

- a helper, wrapper or constant used exactly once - inline it
- a variable that only forwards a value into the next line
- an interface, factory or layer introduced for a single implementation
- a parameter, import, field or branch nothing reaches
- duplication: within the diff, or against something that already existed in the repo and got rebuilt
- debug output, commented-out attempts, `TODO`s nobody asked for
- unused imports: run `~/.claude/hooks/unused-imports.sh` for the candidate list, then check each one in the file before deleting - an extension function, an operator or a decorator is used without its name appearing
- comments that restate the code
- anything the task never asked for

Apply what is safe and behaviour-preserving, in one pass. Do not touch behaviour, do not fix bugs, do not rename public API - that is separate work, and mention it rather than doing it.

Skip code you did not write in this session unless your change made it wrong.

## 2. Docs

Find the docs that actually reference what changed - grep the repo for the touched class, endpoint, command, config key or flag. Then ask, do not write:

> Docs: `README.md` ("Setup" section) and `docs/api.md` name the endpoint you changed. Update both, one, or neither?

Only skip the question when I already named the docs in the task - then just do it. If nothing references the change, one line saying so.

## Report

- **Removed** - what you cut, one line each, with `file:line`
- **Left alone** - what looked cuttable but was not safe, one line each with why. Write "nothing" if there is nothing.
- **Docs** - the question, or what you updated because I asked for it

Nothing to cut? Say "diff is clean" and go straight to the docs step. Do not invent work.

Related: `/mw-next-tidy` suggests one single tidy step and touches nothing - use that mid-task. This one is the end-of-task pass and applies the changes.
