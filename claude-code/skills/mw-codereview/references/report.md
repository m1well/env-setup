# The report

Report mode writes `review.md` and `findings.json` into the dated output folder; session mode
answers in the chat ("Session result" below). Section headings, labels, severities, priorities
and ids stay in English, so two reviews stay comparable and greppable; titles and prose follow the
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

Ids are stable across runs. A finding carried from the baseline keeps its `F` id; a new one takes
the next free number. The overview stays sorted by priority, so the ids may jump.

## Format

```markdown
# Code review <repo name> - <YYYY-MM-DD>

<stack line(s) from the digest>
Scan: <files> files, <hits> hits, <n> findings, <r> recommendations, <m> discarded. Tools: <ran>. Not run: <missing>.
Correctness: `/code-review high` on <dir>, <dir> - <k> findings kept, <d> discarded.
<only with a baseline:> Since <date of the baseline>: <new> new hits, <resolved> resolved; <o> findings still open, <f> fixed.
<instead, when the digest says so:> Code unchanged since <date> - findings carried over, `/code-review` on <dir> only.

## Overview

| ID | Prio | Severity | Category | Finding | Where |
|---|---|---|---|---|---|
| F01 | P1 | critical | secrets | <title> | `path/File.kt:42` |

**First:** F01 - <one sentence why this one>.

## Authorization model

Keycloak <version>, Hibernate <version>, tenant from <claim mandant_id | Organizations | issuer | none>,
isolation <from the digest>. Anything not seen in the repo is marked "assumed".

| Concept | Where | Rating |
|---|---|---|
| rbac | `SecurityConfig.kt:46` converter, 264 role checks | good - one converter, client roles only |
| tenant isolation | RLS on 51 of 59 tenant tables, all forced | improvable - three tables without a reason, F04 |

**Expected but missing:** <concept the project type needs and the code lacks, or "none">.

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

A repo without a schema (frontend only) gets one line instead of the table: "**Protection need: not
computable** - no schema in this repo; the forms collect <fields>."

## Findings

### F01 · P1 · critical · secrets · SEC-5 · OWASP A07
(privacy findings: `### F07 · P2 · high · privacy · GDPR Art. 9`, correctness: `### F09 · P3 · medium · correctness`)
**<title - what is wrong, in one line>**

- **Where:** `path/File.kt:42`, plus every further location (or "16 endpoints, list below")
- **Evidence:** the redacted line or the count, and the scan ids it came from (`h3`, `h17`)
- **Status:** confirmed | suspicion - <what is missing to confirm>
- **Detail:** two or three sentences: what happens, who can trigger it, why it matters here
- **Fix:** the concrete change, as code when it fits in a few lines

### Carried over, unchanged

Low findings from earlier runs that nobody touched, one row each instead of a full block:

| ID | Finding | Where | Open since |
|---|---|---|---|
| F14 | <title> | `path/File.kt:12` | 2026-10-20 |

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

## Discarded and accepted

- `h12` SB-SQL-CONCAT `RaceRepository.kt:40` - concatenates an enum name
- `SB-NO-VALID` x22 - discarded 2026-10-20, unchanged: DTOs are validated in the service
- `DUP-BLOCK` x3 `index.html` - accepted: one copy per app on purpose

## Applied in this run

<only when the user asked for fixes after the report>
- F01 `application.yml:12` - value moved to `${API_KEY}`; tests `:app:test` green
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
- **Authorization model**: one row per concept of `--show authz`, plus tenant isolation when there
  is a tenant. Rating `good`, `improvable`, `problematic` or `replace`, half a sentence why, and the
  finding or recommendation id. `good` rows stay - they say what to keep.
- **Privacy profile table**: every `high` and `very high` table, and every other table whose purpose
  fit is "no" or "unclear". The rest in one line: "<n> further tables with contact data only".
  Column and table names, never values.
- Nothing in the report that the scan output already says better - no copy of the digest, no
  summary paragraph at the end.

## findings.json

The scanner pre-fills it with what it carried; you complete it. The next run reads it, re-anchors
every open finding (`still there`, `moved`, `anchor gone`) and skips the decided hits.

```json
{"date": "2026-10-27", "scope": "full",
 "reviewed_dirs": ["backend/src/main/kotlin/app/billing"],
 "findings": [{"id": "F01", "key": "SB-CFG-SECRET:application.yml", "title": "...", "priority": "P1",
               "severity": "critical", "category": "secrets", "status": "open", "first_seen": "2026-10-20",
               "file": "src/main/resources/application.yml", "line": 12, "anchor": "api-key:", "hits": ["<hit key>"]}],
 "decisions": [{"key": "<hit key>", "check": "SB-NO-VALID", "file": "...", "line": 40,
                "verdict": "discarded", "reason": "...", "date": "2026-10-20"}]}
```

- `key`: the check id plus the place, or a short slug for reader findings. Stays the same across runs.
- `anchor`: a short code fragment of the line that identifies it - an identifier, never a value.
- `status`: `open` or `fixed`; `first_seen` stays from the run that found it.
- `reviewed_dirs`: the `/code-review` targets of this run.
- `decisions` are written with `--decide`, not by hand.

## Session result

The chat answer of session mode, in the user's language:

```markdown
**Scope:** branch `feature/x` against `origin/main`, 14 files - <stack line>
Scan: <hits in scope> hits, <n> findings, <m> discarded. `/code-review high <target>`: <k> kept.

| ID | Prio | Severity | Finding | Where | Status |
|---|---|---|---|---|---|
| F01 | P1 | high | <title> | `File.kt:42` | fixed |
| F02 | P2 | medium | <title> | `File.kt:80` | open - suspicion, needs <what> |

**Tests:** `./gradlew :api:test` green / <failures with output>
**Changed:** `File.kt`, `Other.kt`
**Not checked:** <tools, sampled checks>
```

Discarded hits go into one line: "Discarded: h12, h40 (reason), ...". Findings outside the scope that
block the scope (a broken security chain) are named, not fixed.
