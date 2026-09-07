---
name: mw-count-overall
description: Counts what a codebase is made of - files, lines split into code, comments and blanks, declared types (classes, interfaces, enums, records, objects, type aliases), Spring and Angular annotations, a production/test/docs split, and the largest files. Language-agnostic, works in any repo. Use when asked how big something is, what it consists of, how much of it is tests, or how comment-heavy it is. Also invoked via /mw-count-overall.
argument-hint: [path - optional, defaults to the current directory]
allowed-tools: Bash(python3:*)
---

# Count overall

## Run it

```
python3 ~/.claude/skills/mw-count-overall/count.py [path]
```

The path comes from `$ARGUMENTS`, or the current directory if there is none. Point it at a module or subdirectory to count just that part.

Options: `--json` when you need to calculate from the numbers rather than show them, `--all` to include lock files and minified output, `--top N` for a longer largest-files list.

## Show it

Paste the tool output as it is, inside a code block. Do not rebuild the tables by hand and do not round the numbers - the whole point is that the count is reproducible.

Then at most three lines of reading, and only where a number actually says something: a comment share far off the rest of the codebase, a test ratio near zero, a single file dwarfing every other one. If nothing stands out, say the numbers look unremarkable and stop. No summary of what the table already shows.

## What the numbers are worth

Solid: file counts, line splits, the language table.

Approximate, and say so if it matters for the question:
- a line counts as a comment only when it starts with one, so `foo() // why` is a code line. String literals are masked first, so `"// text"` is not mistaken for a comment
- types are found by regex per line, not by a parser: nested, anonymous and inner classes are missed, and so is anything declared across several lines
- functions and methods are deliberately not counted - no regex gets that right across Kotlin, Java and TypeScript, and a wrong number is worse than none
- the production/test/docs split goes by path and filename. Docs wins first: every Markdown and text file, everything under `docs/`, `doc/`, `documentation/`, `adr/`, `rfc/`, `wiki/`, `manual/`, `guides/` whatever its extension, plus README, CHANGELOG, CONTRIBUTING, LICENSE and their siblings. Then tests, by `src/test/`, `__tests__/`, `*.spec.ts`, `*Test.kt` and the usual suffixes. Everything left is production, so a project naming its tests differently inflates production

File selection uses `git ls-files` inside a repository, so `.gitignore` decides what is in scope. Outside a repository it walks the tree and skips the usual build and dependency directories. Lock files and minified output are always skipped unless `--all` is given; the header line says how many files that was.
