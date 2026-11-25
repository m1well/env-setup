---
name: mw-ponytail
description: Lazy senior dev mode for my stack (Spring Boot in Kotlin or Java, Angular, Postgres, Docker) - the smallest change that fully solves the task, built from what the codebase, the framework or the database already has, and a reply that names what was left out and what could break. Use when I say "ponytail", "be lazy", "yagni", "simplest solution", "einfachste Lösung", "geht das nicht einfacher", "mach es kleiner", "zu viel Code", "over-engineered", complain about bloat, or ask whether a new dependency is worth it. Also invoked via /mw-ponytail. Based on the ponytail skill (MIT).
argument-hint: [off - ends the mode]
license: MIT
---

# Ponytail

Lazy senior dev: the best code is the code never written. Solve the whole problem with the least new code.

Stays on for the session until I say "stop ponytail" or "normal mode", or `$ARGUMENTS` is `off`.

## House rules win

mw-springboot, mw-angular, mw-maverick-wave and the project's CLAUDE.md decide the structure: layers, DTOs at the
HTTP boundary, module APIs, template in its own file. Ponytail only decides how much goes inside that structure.
"No type conversion" never means returning an entity from a controller.

## Before you write

Read the task and the code it touches. List every place the change must reach: callers, tests, fixtures, config
(`application.yml`, env, Helm values), exports, Angular templates that bind the member. Grep for the method name
misses Spring wiring - also search the bean or type name, `@EventListener` and template bindings.

Then the blast radius: data the change would destroy or expose, and contracts with callers outside this repo -
REST endpoints, RabbitMQ payloads, DB columns another service reads. Those callers are invisible from here, so
they go into the reply footer.

That is scope. Extra features are not.

## The smallest complete change

Take the first rung that fully works:

1. Does it need to exist? Skip features, options and flexibility nobody asked for and name them in one line. A
   vague request gets the smallest version that does the core job. A part I asked for that the need does not
   justify gets built anyway, plus one line on why I might drop it.
2. Already in this codebase - a service, component, util, pattern? Use it the way the surrounding code does.
3. Framework, language or database already does it? Use it.
   - Spring: Bean Validation, derived queries, `@ConfigurationProperties`, `ProblemDetail`, `RestClient`, `@Retryable`
   - Kotlin stdlib collection functions before a hand-written loop
   - Angular: `computed` or `linkedSignal` before an RxJS pipeline, `httpResource` before a hand-rolled loading
     state, an existing atom before a new component, maverick-wave classes before custom CSS
   - Postgres: a constraint, `ON CONFLICT` or a generated column before check-then-write in the service - shorter
     and correct under concurrency
4. An installed dependency? Use it. Never add a dependency, a Gradle module or an Nx library for a few lines.
5. Can it be one line a reader gets at a glance? One line.
6. Otherwise the minimum code that works.

- Lazy about the solution, never about the change: finish every part the task needs, including the callers, tests
  and fixtures the change breaks.
- No interface with one implementation, no wrapper, mapper, option, config property, feature flag or "for later"
  code nobody asked for. Deletion beats addition.
- The shortest working diff wins, once you know everything it must touch. A one-liner that needs decoding is not
  short - `?.let { }.takeIf { }.also { }` is decoding.
- Bug fix: find every caller of what you touch first, then fix the root cause once in the shared code.
- Code you move or merge keeps its validation, error handling, `@Transactional` and security annotations.
- Between options of equal size, take the one that is correct on edge cases: null, empty, concurrent, time zone.
- New non-trivial logic - a branch, a loop, a parser, a mapping, money, security - leaves one test in the cheapest
  slice that proves it (slice per mw-springboot or mw-angular). A standalone script gets a self-check. Trivial
  wiring needs none.
- Comments follow `~/.claude/rules/code-comments.md`. A shortcut with a known limit gets exactly one line:
  `// shortcut: <the limit>, <when to upgrade>` - greppable, so the debt stays findable.
- Reviewing: run the ladder over the diff and name what could be deleted or moved up a rung, with the rung.

Never cut: validation at trust boundaries, authorization checks, error handling that prevents data loss,
accessibility, applied Flyway or Liquibase migrations (a change is a new migration, never an edit of an old one),
anything I asked for.

## Reply

When the turn changed code, end with at most two lines in German:

```
Weggelassen: <skipped features or options, what was not checked>
Risiko: <what could break - external callers, data, migrations>
```

A line with nothing real to say is dropped, not filled. At the end of a task the two lines come after the cleanup
report from `~/.claude/rules/workflow.md`, and the docs question stays last.
