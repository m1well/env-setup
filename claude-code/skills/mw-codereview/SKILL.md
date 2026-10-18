---
name: mw-codereview
description: Whole-repository code review for Spring Boot (Kotlin or Java, Gradle or Maven) and Angular (Nx or classic) in one pass, security first. A deterministic Python scanner finds the candidates - security filter chains and an authorization matrix of every endpoint, guarded routes, injection and XSS sinks, secrets incl. git history, Keycloak hardening (resource server, admin client, realm exports, keycloak-js), framework versions against 2026 CVEs and EOL dates - and then the design - calls between services and frontend, module cut of Gradle modules and Nx libs, database design against the migrations, write paths no test reaches, forms and deletes that non-technical users trip over, duplicated code and shared candidates - and a privacy profile of the data model: which tables hold personal and special-category data (GDPR Art. 9), the protection need and a score, whether the app needs what it collects, erasure paths, consent proof, personal data in logs, responses and URLs, third parties and tracking. Claude Code's built-in /code-review adds a correctness pass on the hotspot directories. Claude verifies and rates. Ends in a prioritized report with a privacy profile plus low-priority recommendations. Use whenever someone wants a code review, security review, privacy or GDPR review, audit, architecture review, health check or quality check of a whole repository, backend, frontend or monorepo. Also invoked via /mw-codereview.
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
first in every step - in what you open, in how much time it gets, in the order of the report.
The design passes come after it and get real time too: a thorough review may take long.

The scanner matches patterns; it does not follow logic. That part comes from Claude Code's
built-in `/code-review`, started on the riskiest directories right after the scan. It runs in the
background while you work through security and design, and its findings join the report.

One pass, start to finish. No stages, no AskUserQuestion. The only reason to stop early is a
path that does not exist.

## 1. Run the scanner

The path comes from the arguments, `.` when there is none.

```bash
SKILL=~/.claude/skills/mw-codereview
python3 $SKILL/scripts/scan.py <path> --online --resolve
```

- The output folder is `<path>/docs/mw-codereview-<today>/`; the digest prints it. That is `OUT`
  below, and `review.md` goes there too. An earlier run's folder stays untouched.
- `--online` lets npm audit, osv-scanner, trivy and semgrep (default and OWASP Top 10 rules) use
  their databases. They send package names and versions, never source. Drop it when the user said
  offline or confidential.
- `--resolve` asks Gradle or Maven for the resolved runtime classpath, so the CVE floors see the
  transitive Tomcat, Jackson and Spring Security versions instead of only the pinned ones. It runs
  the build tool and can take a few minutes. If the `resolve` line in the digest shows an error,
  say so in the report - the `DEPS-BOOT-MANAGED` hits then stand in for it.
- The newest earlier `docs/mw-codereview-*/scan.json` is the baseline automatically: each hit gets
  `[new]` when it was not there before, and the summary counts what was fixed since.

The digest it prints is your working list: stack, tools, inventory (endpoints, routes, modules,
Nx projects, calls, schema, test reach, Keycloak, duplication) and every check with its hits,
sorted by severity with security first. Details:

```bash
python3 $SKILL/scripts/scan.py --out "$OUT" --show SB-SQL-CONCAT,NG-DOM-XSS   # checks or hit ids
python3 $SKILL/scripts/scan.py --out "$OUT" --show endpoints   # or routes, modules, projects, calls,
                                                               # entities, privacy, hotspots, keycloak, owasp
```

`--show owasp` maps the hits to OWASP Top 10:2025 and names the categories no check covers -
those are reader work. `--list-checks` prints the whole catalogue (about 260 checks). If the digest
says no Spring Boot or Angular was found, review the repository-level hits only and say so in the
first line of the report.

## 2. Start the correctness review

```bash
python3 $SKILL/scripts/scan.py --out "$OUT" --show hotspots
```

lists the source directories that carry the most hit weight. Pick the targets from the top - one
on a small repo, up to three on one over 400 files - and prefer directories that move money,
delete data, decide permissions or hold the special-category data of the privacy profile. For each
target call the skill `code-review` through the Skill tool with `high <directory>` as arguments:
one directory per call, nothing else on the line.

- Never `ultra` (billed, started by the user only), never `--fix` or `--comment`.
- It runs as a background subagent. Go on with step 3; its findings arrive when it is done.
- If the call is refused or the skill is missing, put "not run" and the exact command
  (`/code-review high <dir>`) into "Not checked" and go on.

## 3. Evaluate - security first

Work through it in this order. `references/evaluation.md` has the per-area details, the false
positive patterns, and how to read a security chain.

1. **Critical and high security hits, every one of them.** Open the file at the line (Read with an
   offset), and the caller when the hit depends on where a value comes from. Decide: *confirmed*,
   *suspicion* (needs runtime, another system or the deployment), or *false positive*. The
   `verify:` line under each check says what decides it.
2. **Authorization, read by hand.** Read every file that defines a `SecurityFilterChain`
   completely - they are short and they are the most important file in the backend. Then go
   through `--show endpoints` and `--show routes`. The scanner already flags public writes,
   unmatched paths and siblings that disagree. What it cannot see, you check - the list is in
   `references/evaluation.md`, section "What only a reader sees": object-level access (IDOR),
   tenant isolation, the login and token flow, webhooks and uploads, and whether frontend and
   backend agree about auth, CSRF and CORS.
3. **Keycloak**, when the digest has a `keycloak` line: read `references/keycloak.md` and do its
   checks - roles, audience, `sub` as the user key, tenant from the token, the admin client, the
   realm. `KC-REALM-LOCAL` is the hardening list for the realm that serves real users.
4. **Medium security hits**: verify up to five per check, then judge the pattern from those.
5. **Low security hits**: aggregate per check. Open one sample at most.
6. **Tools that did not run** go into the report's "Not checked" section with the install hint
   from the digest. A review that did not run osv-scanner must not read like one that did.

## 4. Design passes

Six passes, each with its scanner hits and its reader checks. Do all six.

| pass | hits | inventory | reader checks |
|---|---|---|---|
| calls between systems | `ARCH-*` call checks, `SB-TX-REMOTE-CALL`, `SB-HTTP-NO-TIMEOUT` | `--show calls` | `references/architecture.md` |
| module cut | `ARCH-MODULE-*`, `ARCH-ENTITY-SHARED`, `NX-*`, `SB-PACKAGE-CYCLE` | `--show modules`, `projects` | `references/architecture.md` |
| database design | `DB-*`, `SB-ENUM-ORDINAL`, `SB-EAGER`, `SB-ENTITY-*` | `--show entities` | `references/quality.md` |
| test gaps | `TESTGAP-*`, `SB-UNTESTED`, `NG-NO-SPEC` | the `tests` line | `references/quality.md` |
| usability and reuse | `UX-*`, `DUP-*`, `REUSE-*` | - | `references/quality.md`, `architecture.md` |
| privacy | `PII-*` | `--show privacy` | `references/privacy.md` |

The privacy pass also writes the report's "Privacy profile": the protection need, which tables
hold what about whom, whether the app's purpose needs it, and what follows if it leaks. The
`PII-*` checks marked security in the digest belong to step 3 as well.

`UX-DELETE-NO-CONFIRM` is checked hit by hit: open the handler, follow the event to the code that
changes data, and look for any confirmation on the way. Every other design check: verify up to
five hits, then judge the pattern.

On a repository with more than about 400 source files, hand the six passes to parallel subagents
(Agent tool, general-purpose) once step 3 is done. Each gets `OUT`, its `--show` commands, its
reference file and `references/report.md`, reads the code itself, and returns findings and
recommendations in the report format. You merge them, remove duplicates with step 3, and re-rate.

On a large repo you still cannot open everything. Spend the reading on security first, then on
the paths that move money, delete data or decide permissions. Say what you sampled, and never
present a sampled check as fully verified.

## 5. Turn hits into findings and recommendations

A hit is a line the scanner matched. A finding is a problem a person can fix. A recommendation is
a structural change that makes the next changes cheaper. The rules:

- **One cause, one finding.** Sixteen endpoints without `@Valid` is one finding with a count and
  a location list, not sixteen. Same secret reported by gitleaks and by `REPO-SECRET-TOKEN` is one.
- **Migration status is a ratio.** "45 of 45 components set OnPush explicitly" - one finding.
- **Every finding names a file and line, a class, or a count.** If it would be true without
  having opened this repo, it is not a finding.
- **Module and lib cut, shared candidates, merged copies are recommendations** - unless they leak
  data or break a rule the project set itself (`ARCH-ENTITY-SHARED`, `NX-SHARED-UPWARD`).
- **False positives are listed**, one line each, so the next run's reader knows they were looked at.
- **`/code-review` findings are hits too**, from a reviewer that never saw the scan. Open each at the
  line and keep it only if you can name the input that breaks it. Category `correctness`, evidence
  `/code-review high <dir>`. One that a scanner hit already covers merges into that finding. Write
  `review.md` only after every review you started has reported back - if nothing else is left to
  do, end the turn with one line naming the review you wait for.
- **Re-rate after reading.** A `high` SQL concatenation of an enum is gone; a `medium` CSRF hit on
  a cookie session is `critical`. The scanner's severity is a starting point.
- **Name the rule** when one applies: the `mw-springboot` / `mw-angular` id from the digest
  (SEC-3, LAYER-7, MODEL-9, TEST-4, ...), the OWASP Top 10:2025 id for security findings, and the
  GDPR article for privacy findings.

Severity, priority, recommendations and the exact format are in `references/report.md`.

## 6. Write the report

Write `$OUT/review.md` in the format of `references/report.md`, in the language the user writes in.
Check ids, file paths, class names and code stay as they are. Secret values never appear - the
scanner redacts them (`abc***(32 chars)`), keep it that way in the report and in the chat.

Then answer in the chat with: the stack line, the protection need with the score, the counts per
priority, the P1 findings with one line each, the number of recommendations, and the path to
`review.md`. Nothing else - the report holds the rest.

## Rules

- **Read-only.** Nothing in the scanned repo changes except `$OUT`. No fixes, no formatting, no
  dependency updates, no build or test run - those come after the user read the report. That holds
  for `/code-review` too: no `--fix`, no `--comment`.
- **Personal data stays out of the report.** Table and column names yes, values never - not from
  seed files, not from fixtures, not from a log line.
- **The scanner is the source of the hits.** Do not grep the repo for your own variant of a check
  and mix the result in silently. A thing you found by reading goes into the report as yours,
  with the file and line.
- **Version data has a date.** The digest prints it (`version data from ...`). Older than three
  months: say in the report that the CVE floors and EOL dates may be stale, and prefer the npm
  audit / osv-scanner results where they disagree.
- **Old runs stay.** A new run gets a new dated folder; an earlier `review.md` is never edited.
