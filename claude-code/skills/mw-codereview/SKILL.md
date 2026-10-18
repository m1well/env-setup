---
name: mw-codereview
description: Code review for Spring Boot (Kotlin or Java, Gradle or Maven) and Angular (Nx or classic), security first - of a whole repository with a documented report, or of one branch or directory with the findings fixed right away. A deterministic Python scanner finds the candidates - security chains and an authorization matrix of every endpoint, the authorization model and tenant isolation (roles, ownership, interceptors, Keycloak Organizations, RLS, tenant context in async code and caches), injection and XSS sinks, secrets incl. git history and ignored files that end up in the artifact, Keycloak hardening, framework versions against CVEs and EOL dates - then the design (calls, module cut, database, correctness, untested writes, usability, duplication) and a GDPR privacy profile of the data model. Claude Code's /code-review adds a correctness pass on the hotspots; Claude verifies and rates. Ends in a prioritized report or in fixes. Use whenever someone wants a code review, PR or branch review, security, authorization, multi-tenancy, privacy or GDPR review, audit, architecture review, health check or quality check of a repository, backend, frontend or monorepo. Also invoked via /mw-codereview.
argument-hint: [path - empty means the current directory]
allowed-tools: Bash(python3:*)
---

# Code review

The work is split in two, and the split is the point. The scanner reads every file of the repo
the same way every time: regexes over masked source, a bracket-aware model of each class, the
build files, the security config, the route tables, the migrations, the templates, and whatever
external scanner is installed. It decides nothing. Every hit is a candidate with evidence and a
hint on how to verify it.

**Your job is the judgement**: open the code behind the hits, throw out the false positives,
merge what has one cause, rate it, and add the things only a reader can see. Security comes
first in every step - in what you open, in how much time it gets, in the order of the result.

The scanner matches patterns; it does not follow logic. That part comes from Claude Code's
built-in `/code-review`, started on the riskiest directories right after the scan. It runs in the
background while you work through security and design, and its findings join the result.

## 0. Ask for the scope

One AskUserQuestion before anything else, in the user's language:

| option | reviews | result | changes in the repo |
|---|---|---|---|
| whole repository, documented | every file | `review.md` and `findings.json` in `docs/mw-codereview-<date>/` | that folder only; fixes later, on request |
| one branch, fix directly | files changed against the base branch, incl. uncommitted and untracked | the chat at the end | the fixes |
| one directory, fix directly | the directory the user names | the chat at the end | the fixes |

Skip the question when the request already answers it ("review this branch", "only the billing
module", "full audit with report"). The first option is **report mode**, the other two are
**session mode**. On the base branch itself a branch review covers the uncommitted changes; when
there are none, say so and ask for a directory. After this question, one pass to the end.

## 1. Run the scanner

The path comes from the arguments, `.` when there is none.

```bash
SKILL=~/.claude/skills/mw-codereview
python3 $SKILL/scripts/scan.py <path> --online --resolve         # report mode
python3 $SKILL/scripts/scan.py <path> --online --diff [base]     # session mode, branch
python3 $SKILL/scripts/scan.py <path> --online --focus <dir>     # session mode, directory
```

- Report mode writes to `<path>/docs/mw-codereview-<today>/`, session mode to a folder in the temp
  directory, so nothing lands in the repo but the fixes. The digest prints it; that is `OUT` below.
- In session mode the scanner still reads the whole repo - security chains, routes and the schema
  need it - but the digest lists only hits inside the scope. Other hits stay in `scan.json`.
- `--online` lets npm audit, osv-scanner, trivy and semgrep use their databases. They send package
  names and versions, never source. Drop it when the user said offline or confidential.
- `--resolve` asks Gradle or Maven for the resolved runtime classpath, so the CVE floors see the
  transitive versions and osv-scanner gets an SBOM. It runs the build tool and takes a few minutes;
  in session mode use it only when the scope touches a build file. A `resolve` error goes into the
  result - the `DEPS-BOOT-MANAGED` hits then stand in for it.
- The newest earlier `docs/mw-codereview-*/scan.json` is the baseline automatically. Hits get
  `[new]`; the `baseline` line says what changed since, or that the code is unchanged; the
  `carried` line brings the open findings and the decided hits of the `findings.json` next to it.
- The `changes` line names the security-relevant files changed against the base branch, deleted
  ones too. A removed filter or a dropped CORS origin fires no check - read them in step 3.

The digest is your working list: stack, tools, inventory (endpoints, routes, modules, Nx projects,
calls, schema, test reach, Keycloak, duplication), vulnerable packages one line each, secrets one
line per distinct value, then every check with its hits, sorted by severity with security first.

```bash
python3 $SKILL/scripts/scan.py --out "$OUT" --show SB-SQL-CONCAT,NG-DOM-XSS   # checks or hit ids
python3 $SKILL/scripts/scan.py --out "$OUT" --show endpoints   # or routes, modules, projects, calls, entities,
          # privacy, authz, hotspots, keycloak, owasp, tools, changes, findings, decided
```

`--show owasp` maps the hits to OWASP Top 10:2025 and names the categories no check covers -
those are reader work. `--list-checks` prints the catalogue. If the digest says no Spring Boot or
Angular was found, review the repository-level hits only and say so in the first line.

**Config files and secrets are read only through the scanner:**

```bash
python3 $SKILL/scripts/scan.py <path> --cat <file>[:from-to]
```

It prints the file with every secret-like value masked the way the digest masks it. Use it for
`application*.yml`, `.properties`, `.env`, realm exports, and every file with a secret hit -
tracked, untracked or ignored, and inside a built jar (`build/libs/app.jar!BOOT-INF/classes/application.yml`). Never Read, cat, sed or grep such a file: one unmasked value in the
transcript is a leak.

## 2. Start the correctness review

```bash
python3 $SKILL/scripts/scan.py --out "$OUT" --show hotspots
```

lists the source directories with the most hit weight. Decided hits do not count, new hits count
double, and tags raise or lower a directory: `[security]`, `[public]`, `[pii]` and `[new code]` up,
`[reviewed]` (by /code-review in the baseline run) down.

- **Report mode:** one directory on a repo up to 300 source files, two above that, plus every
  directory tagged `[new code]`. When the digest says the code is unchanged since the baseline,
  one directory no run has reviewed yet - the carried findings cover the rest.
- **Session mode:** one call on the scope - the branch name, or the directory.

Call the skill `code-review` through the Skill tool with `high <directory or branch>` as arguments,
one target per call, nothing else on the line.

- Never `ultra` (billed, started by the user only), never `--fix` or `--comment`.
- It runs as a background subagent. Go on with step 3; its findings arrive when it is done.
- If one stops on a rate or spend limit (429), continue that same agent with SendMessage once
  instead of starting it again - the work it did is kept. A second failure counts as not run.
- Refused, missing or not run: put "not run" and the exact command (`/code-review high <dir>`)
  into "Not checked" and go on.

## 3. Evaluate - security first

Work through it in this order. `references/evaluation.md` has the per-area details, the false
positive patterns, and how to read a security chain.

1. **Carried state.** Hits decided in an earlier run (`--show decided`) are not verified again -
   changed evidence gives a hit a new key, so a decided hit is unchanged. Carried findings
   (`--show findings`): `still there` and `moved` stay open under their id; `anchor gone` or
   `file gone` - open the place and mark it fixed or re-anchor it.
2. **Critical and high security hits, every one of them.** Open the file at the line (Read with an
   offset), and the caller when the hit depends on where a value comes from. Decide: *confirmed*,
   *suspicion* (needs runtime, another system or the deployment), or *false positive*. The
   `verify:` line under each check says what decides it.
3. **Authorization, read by hand.** Read every file that defines a `SecurityFilterChain`
   completely, and every security-relevant file of the `changes` line. Then `--show endpoints` and
   `--show routes`. What the scanner cannot see is listed in `references/evaluation.md`, section
   "What only a reader sees".
4. **Authorization model and tenancy**, when the digest has an `authz` line: `--show authz`, then
   `references/authorization.md`. The ratings fill the report's "Authorization model" table.
5. **Keycloak**, when the digest has a `keycloak` line: `references/keycloak.md`.
6. **Medium security hits**: verify up to five per check, then judge the pattern from those.
7. **Low security hits**: aggregate per check. Open one sample at most.
8. **Tools that did not run**, or ran with a `note` like "0 Gradle packages read", go into "Not
   checked" with the hint from the digest. A review that did not run osv-scanner must not read
   like one that did.

## 4. Design passes

Seven passes, each with its scanner hits and its reader checks. Report mode does all seven. Session
mode does the ones the scope touches, on the changed code only - no module recommendations for a
branch.

| pass | hits | inventory | reader checks |
|---|---|---|---|
| calls between systems | `ARCH-*` call checks, `SB-TX-REMOTE-CALL`, `SB-HTTP-NO-TIMEOUT` | `--show calls` | `references/architecture.md` |
| module cut | `ARCH-MODULE-*`, `ARCH-ENTITY-SHARED`, `NX-*`, `SB-PACKAGE-CYCLE`, `DEPS-UNUSED`, `DEPS-BUILD-IN-PROD` | `--show modules`, `projects` | `references/architecture.md` |
| database design | `DB-*`, `SB-ENUM-ORDINAL`, `SB-EAGER`, `SB-ENTITY-*` | `--show entities` | `references/quality.md` |
| correctness | `SB-DST-DURATION`, `SEED-INSERT-ONLY`, `SB-LIMIT-UNUSED`, `DB-NATIVE-COUNTER-OVERWRITE` | - | `references/quality.md` |
| test gaps | `TESTGAP-*`, `SB-UNTESTED`, `NG-NO-SPEC` | the `tests` line | `references/quality.md` |
| usability and reuse | `UX-*`, `DUP-*`, `REUSE-*` | - | `references/quality.md`, `architecture.md` |
| privacy | `PII-*`, `TOKEN-NO-EXPIRY`, `SB-TOKEN-IN-LOG` | `--show privacy` | `references/privacy.md` |

The privacy pass also writes the report's "Privacy profile". The `PII-*` and `DB-*` checks marked
security in the digest belong to step 3 as well.

`UX-DELETE-NO-CONFIRM` is checked hit by hit: open the handler, follow the event to the code that
changes data, and look for any confirmation on the way. Every other design check: verify up to
five hits, then judge the pattern.

On a repository with more than about 400 source files, hand the passes to parallel subagents
(Agent tool, general-purpose) once step 3 is done. Each gets `OUT`, its `--show` commands, its
reference file, `references/report.md` and the `--cat` rule, reads the code itself, and returns
findings and recommendations in the report format. You merge them, remove duplicates, and re-rate.

On a large repo you still cannot open everything. Spend the reading on security first, then on
the paths that move money, delete data or decide permissions. Say what you sampled, and never
present a sampled check as fully verified.

## 5. Turn hits into findings

A hit is a line the scanner matched. A finding is a problem a person can fix. A recommendation is
a structural change that makes the next changes cheaper.

- **One cause, one finding.** Sixteen endpoints without `@Valid` is one finding with a count and
  a location list. One package with 40 advisories from three tools is one finding (the `vulns`
  line); one secret value from three tools is one (the `secrets` line).
- **Migration status is a ratio.** "45 of 45 components set OnPush explicitly" - one finding.
- **Every finding names a file and line, a class, or a count.** If it would be true without
  having opened this repo, it is not a finding.
- **Module and lib cut, shared candidates, merged copies are recommendations** - unless they leak
  data or break a rule the project set itself (`ARCH-ENTITY-SHARED`, `NX-SHARED-UPWARD`).
- **Record every verdict on a hit**, so the next run does not ask again:
  `python3 $SKILL/scripts/scan.py --out "$OUT" --decide h12,h40,SB-NO-VALID discarded "<reason>"`.
  `accepted` instead of `discarded` for hits that are real but intended and documented (a copied
  `index.html` per app). Hit ids and check ids both work.
- **`/code-review` findings are hits too**, from a reviewer that never saw the scan. Open each at the
  line and keep it only if you can name the input that breaks it. Category `correctness`, evidence
  `/code-review high <target>`. One that a scanner hit already covers merges into that finding.
  Style findings - comments, naming, formatting, a project's style rules - are dropped without a
  line. Write the result only after every review you started has reported back; if nothing else
  is left to do, end the turn with one line naming the review you wait for.
- **Re-rate after reading.** A `high` SQL concatenation of an enum is gone; a `medium` CSRF hit on
  a cookie session is `critical`. The scanner's severity is a starting point.
- **Name the rule** when one applies: the `mw-springboot` / `mw-angular` id from the digest
  (SEC-3, LAYER-7, MODEL-9, TEST-4, ...), the OWASP Top 10:2025 id for security findings, and the
  GDPR article for privacy findings.

Severity, priority, ids and the exact formats are in `references/report.md`.

## 6a. Report mode - write the report

Write `$OUT/review.md` and complete `$OUT/findings.json` (the scanner pre-fills it with what it
carried) in the format of `references/report.md`, in the language the user writes in. Check ids,
file paths, class names and code stay as they are. Carried findings keep their id.

Then answer in the chat with: the stack line, the protection need with the score, the counts per
priority, the P1 findings with one line each, the number of recommendations, and the path to
`review.md`. The last line says what changed, so a closing check needs no extra round: "Changed:
only `docs/mw-codereview-<date>/`, no other file, no docs affected." Nothing else - the report
holds the rest.

**Fixes on request.** When the user asks for fixes after reading the report: P1 and P2, plus the
P3 and P4 findings whose fix is one or two lines, in priority order. Append "Applied in this run"
to this run's `review.md`, set those findings to `fixed` in `findings.json`, and run the tests of
the touched modules.

## 6b. Session mode - fix and answer

1. Fix every confirmed finding whose fix stays local, in priority order: P1 to P3, plus P4 when it
   is a line or two. The smallest change that removes the cause, in the project's own style.
   Suspicions and recommendations are not fixed - they are listed.
2. Run the tests of the touched modules (`./gradlew :<module>:test`, `mvn -pl <module> test`,
   `npx nx test <project>`), and the linter when it is fast. A failing test is reported with its
   output; a test changes only when the test itself was wrong.
3. Answer in the chat, in the format of `references/report.md`, section "Session result". No file
   besides the fixes; `OUT` is a temp folder and stays out of the repo.

## Rules

- **Changes stay in scope.** Report mode changes nothing but `$OUT` until the user asks for fixes.
  Session mode changes only what a finding's fix needs - no reformatting, no unrelated refactoring,
  no dependency upgrade beyond a finding's fix. `/code-review` never runs with `--fix` or `--comment`.
- **Secrets never appear.** Config files and files with secret hits are read through `--cat` only.
  Values stay redacted (`abc***(32 chars)`) in the report, in `findings.json` anchors and in the chat.
- **Personal data stays out of the result.** Table and column names yes, values never - not from
  seed files, not from fixtures, not from a log line.
- **The scanner is the source of the hits.** Do not grep the repo for your own variant of a check
  and mix the result in silently. A thing you found by reading goes into the result as yours,
  with the file and line.
- **Version data has a date.** The digest prints it (`version data from ...`). Older than three
  months: say that the CVE floors and EOL dates may be stale, and prefer the npm audit /
  osv-scanner results where they disagree.
- **Old runs stay.** A new run gets a new dated folder; an earlier `review.md` is never edited.
