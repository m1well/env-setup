# The report

`review.md` in the dated output folder. Section headings, labels, severities, priorities and ids
stay in English, so two reviews stay comparable and greppable; titles and prose follow the
language of the session. Plain hyphens only, no long dashes.

## Severity

| severity | means |
|---|---|
| `critical` | exploitable from outside without special conditions, or a live secret in the tree or the history |
| `high` | a security hole with a precondition, a rule the project set itself broken, or possible data loss |
| `medium` | a weakness with a second line of defence elsewhere, or a cost on every change that touches it |
| `low` | consistency, readability, hardening |

Most findings are `medium`. If everything is `high`, nothing is.

Privacy findings: special-category data reachable by people who do not need it is `high`, so is a
card number or a diagnosis in plain text. Personal data in logs, URLs, seed files or a response that
does not show it is `medium`, and so is a missing erasure path or consent proof - a legal duty, not
a hole. Collected-but-unused fields, free text and a third party without a clear agreement are `low`.

## Priority

The report is sorted by priority; inside a priority, security before the rest, then severity.

| priority | gets | means |
|---|---|---|
| `P1` | every `critical`, every confirmed `high` security finding | fix before anything else ships |
| `P2` | other `high`, confirmed `medium` security findings, every security suspicion | this sprint |
| `P3` | remaining `medium` | plan it |
| `P4` | `low` | backlog, or the next time someone is in that file |

A suspicion is never P1. It sits in P2 with the one thing that would confirm it. Privacy findings
that expose data (the `PII-*` checks marked security) are prioritised like security findings, the
others like design findings.

## Findings and recommendations

A finding is a defect or a broken rule: a hole, a delete without confirmation, a write path no test
reaches, a relation that loses data. A recommendation is a structural change that makes the next
changes cheaper: a module or lib cut, a shared component instead of three copies, an event instead
of a sync chain. Recommendations get `R01` ids, no severity and no priority - they all sit below
P4 - and are sorted by payoff. At most ten; each names what gets cheaper afterwards.

## Format

```markdown
# Code review <repo name> - <YYYY-MM-DD>

<stack line(s) from the digest>
Scan: <files> files, <hits> hits, <n> findings, <r> recommendations, <m> discarded. Tools: <ran>. Not run: <missing>.
Correctness: `/code-review high` on <dir>, <dir> - <k> findings kept, <d> discarded.
<only with a baseline:> Since <date of the baseline>: <new> new hits, <resolved> resolved.

## Overview

| ID | Prio | Severity | Category | Finding | Where |
|---|---|---|---|---|---|
| F01 | P1 | critical | secrets | <title> | `path/File.kt:42` |

**First:** F01 - <one sentence why this one>.

## Privacy profile

**Protection need: <normal | high | very high>** - <the column that decides it, in words>.
Score <s>/100: <p> of <c> columns in <t> of <T> tables are personal; <special> special category,
<high> high-risk, <identifying> identifying. Purpose: <the app's purpose in one sentence>.

| Table | Subjects | Need | What it holds | Purpose needs it? |
|---|---|---|---|---|
| `arbeitstag` | employees | very high | `art` = KRANK, `notiz` | the sick day yes (continued pay), a diagnosis in `notiz` no |

- **One join:** `benutzer` reaches <n> tables - <categories>.
- **Recipients:** <provider (kind, seat) - agreement, transfer basis> or "none found".
- **Worst case:** <two sentences: what a dump or a leaked backup reveals, about whom, and what follows>.
- **Duties:** <only the ones this repo triggers - DPIA, record of processing, processor agreements,
  works council, professional secrecy, retention against deletion>.

## Findings

### F01 · P1 · critical · secrets · SEC-5 · OWASP A07
(privacy findings: `### F07 · P2 · high · privacy · GDPR Art. 9`, correctness: `### F09 · P3 · medium · correctness`)
**<title - what is wrong, in one line>**

- **Where:** `path/File.kt:42`, plus every further location (or "16 endpoints, list below")
- **Evidence:** the redacted line or the count, and the scan ids it came from (`h3`, `h17`)
- **Status:** confirmed | suspicion - <what is missing to confirm>
- **Detail:** two or three sentences: what happens, who can trigger it, why it matters here
- **Fix:** the concrete change, as code when it fits in a few lines

## Recommendations

### R01 · architecture · <title - the change, in one line>
- **Where:** modules, libs or files, with the evidence (`h40`, `--show modules`)
- **Why:** what this costs today, in this codebase
- **Change:** the target cut or the shared piece, with the input or flag that covers the difference
- **Payoff:** what gets cheaper; **Effort:** small | medium | large

## Not checked

- <tool> not installed (`brew install <tool>`) - what that leaves open
- `/code-review` not run (<reason>) - run `/code-review high <dir>` for <dirs>
- <manual check> sampled: <n> of <m>
- version data from <date>

## Discarded

- `h12` SB-SQL-CONCAT `RaceRepository.kt:40` - concatenates an enum name
```

## Rules for the content

- **Title**: the problem, not the category. "Actuator-Endpunkte ohne Login erreichbar", not "Security".
- **Where** is mandatory. A finding without a location or a count is not a finding.
- **Evidence** stays code: identifiers, counts, redacted values. Never a secret in clear text.
- **Detail** says what happens in *this* codebase. "Could be a risk" is not a detail.
- **Fix** is the smallest change that removes the cause. A refactoring plan is a recommendation.
- **Ratios** for migration status: "45 of 45 components", not 45 findings.
- **Rule ids** in the heading when one applies: `mw-springboot` / `mw-angular` ids from the digest,
  OWASP Top 10:2025 (A01-A10) for every security finding, the GDPR article for privacy findings.
- **Privacy profile table**: every `high` and `very high` table, and every other table whose purpose
  fit is "no" or "unclear". The rest in one line: "<n> further tables with contact data only".
  Column and table names, never values.
- Nothing in the report that the scan output already says better - no copy of the digest, no
  summary paragraph at the end.
