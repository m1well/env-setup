---
name: mw-stagereview
description: Fast review of what is staged for the next commit - only the git-added lines, in one Spring Boot or Angular repo or in a folder holding several repos. Runs the mw-codereview scanner with --staged, verifies the security hits on the staged lines, fixes what is confirmed and answers in a short block another agent can act on. No questions, no subagents, no report file. Use when a review of staged changes, the staging area, "vor dem Commit" or the changes a dev agent just made is asked for, typically from a home repo for another repo's path. For a whole repo, a branch or an audit use mw-codereview instead. Also invoked via /mw-stagereview.
argument-hint: [path to the repo or to a folder of repos - empty means the current directory]
allowed-tools: Bash(python3:*)
---

# Stage review

The scanner of mw-codereview reads the whole repo, so security chains and routes are complete, but lists only
the hits on lines the next commit adds. Your job is the judgement on those few hits. One pass, no questions:
the caller is often an agent, and a subagent can neither ask the user nor start subagents.

Needs mw-codereview installed next to this skill.

## 1. Scan

```bash
SCAN=~/.claude/skills/mw-codereview/scripts/scan.py
python3 $SCAN <path> --staged --online
```

- `--online` only matters when a build or lock file is staged: osv-scanner, npm audit and trivy run only then,
  gitleaks reads only the staged diff. Drop it when the user said offline or confidential. Never `--resolve`.
- `focus ... nothing staged`: answer with that one line and stop. Never stage anything yourself.
- The digest prints `OUT`. `--show changes` lists the staged files with the line ranges they add,
  `--show touched` the older hits in the staged files, `--show <CHECK>` one check.

## 2. Verify

1. **Critical and high hits, every one.** Read the file at the line, and the caller when the verdict depends on
   where a value comes from. Decide *confirmed*, *suspicion* (needs runtime or another system) or *false
   positive*. The `verify:` line under each check says what decides it.
2. **Security-relevant staged files** from the `changes` line: read what changed with
   `git -C <dir of the file> diff --cached -- <file name>`. A removed filter, a widened `permitAll`, a dropped
   `@PreAuthorize` or CORS origin fires no check.
3. **Medium hits**: up to three per check, then judge the pattern. **Low**: count only.
4. **`partly staged`**: the line numbers come from the working tree. Check that a hit really sits on staged code.
5. **`not staged`**: name these files in the answer - a new class the commit needs but does not contain breaks
   the next checkout. Do not review or stage them.

`~/.claude/skills/mw-codereview/references/evaluation.md` only when a `verify:` line does not settle a hit,
and then only the section of that area. `--show touched` is not part of this review: one line with the count.

## 3. Fix

Fix confirmed findings - critical to medium, low when the fix is a line or two. The smallest change that removes
the cause, in the project's style. Suspicions are listed, not fixed. Then run the tests of the touched module
(`./gradlew :<module>:test`, `mvn -pl <module> test`, `npx nx test <project>`); a failing test goes into the
answer with its output.

Never `git add`, commit or stash. The fix stays in the working tree, so the answer says which files to add again.

## 4. Answer

In the user's language, check ids, paths and code as they are. Clean:

```
mw-stagereview <path>: 7 staged files, nothing found on the staged lines.
```

Otherwise one line per finding, most severe first, then only the lines that apply:

```
mw-stagereview <path>: 7 staged files, 4 hits on staged lines - 2 fixed, 1 open, 1 discarded
FIXED       [high] SB-SQL-CONCAT OrderRepository.kt:42 - status from the request concatenated into the query
OPEN        [medium] SB-SSRF-INPUT ImportService.kt:18 - suspicion: allow-list lives in the gateway, not visible here
STAGE AGAIN OrderRepository.kt (fixed after staging)
NOT STAGED  backend/src/main/kotlin/de/app/OrderMapper.kt (new)
NOT CHECKED osv-scanner not installed (brew install osv-scanner)
TESTS       ./gradlew :order:test green
OLDER HITS  6 on untouched lines of the staged files
```

## Rules

- **Secrets never appear.** Config files (`application*.yml`, `.properties`, `.env`, realm exports) and files
  with a secret hit are read through `python3 $SCAN <path> --cat <file>:<from>-<to>` only, using the ranges of
  `--show changes` - never Read, cat or `git diff` on them. Values stay redacted in the answer.
- **Changes stay in scope**: only what a finding's fix needs. No reformatting, no refactoring of older code.
- **The scanner is the source of the hits.** Something you saw while reading goes in as yours, with file and line.
- **No subagents, no `/code-review`, no AskUserQuestion.** For more depth the answer can say: run `/mw-codereview`.
