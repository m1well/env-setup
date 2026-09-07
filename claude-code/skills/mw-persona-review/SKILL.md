---
name: mw-persona-review
description: Cognitive walkthrough of a web app through the eyes of a persona with low tech literacy - drives the running app in Chrome, or reviews the frontend code when no browser is connected, and reports every screen, label and error message the persona would not understand. Files a dated report so runs can be compared over time. Invoked via /mw-persona-review.
disable-model-invocation: true
argument-hint: persona=<name> task="<what the persona wants to get done>" [url=<app url>]
---

# Persona Review

Walk through my app as someone who is *not* a developer and report where they would get stuck. This is a cognitive walkthrough, not a user test - it catches the comprehension problems that are obvious in hindsight, cheaply, before a real person hits them.

## Arguments

`$ARGUMENTS` carries `persona=<name>`, `task="<the goal in the persona's own words>"` and optionally `url=<app url>`. Free text works too - pull persona and task out of it. No persona: list the ones you found, one line each, and ask. No task: ask. Never invent a task and never review "the app in general" - a walkthrough without a goal has no stopping point and no verdict.

## 1 - Load the persona

Read `.claude/personas/<name>.md` in the project. `reviews/` in that folder is output, skip it. Nothing there: fall back to `examples/julia.md` or `examples/peter.md` next to this file and note in the report that a generic persona was used - a persona that doesn't know the domain finds weaker things. Offer to copy the closer of the two into `.claude/personas/` as a starting point.

The file is the yardstick for everything below:
- `forbidden_vocabulary` is a hard rule - every hit is a finding, no exceptions
- `known_vocabulary` is its counterpart - those words are fine, don't flag them, or every domain term turns into noise
- `patience` decides when you record an abort
- `device` decides what counts as visible - what's below the fold at 125% zoom is not visible
- `context` decides how much the persona remembers from last time. Usually: nothing

## 2 - Get into the app

**Browser first.** Invoke the `claude-in-chrome` skill, then check whether a browser is actually connected. If it is, the walkthrough runs in the real app - that is the mode that finds things.

The URL comes from `url=`, otherwise derive a candidate from the project (dev script in `package.json`, `docker-compose.yml`, a port in a config) and confirm it with me in one line. **Don't start the app yourself** and don't silently guess a port - walking through a page that isn't there produces a report full of fiction.

**No browser, no connection, or the app isn't running:** say so plainly in one line, then do a **static review** instead of guessing. Read what the project actually uses - Angular templates and their component classes, JSX/TSX, `.vue`, Thymeleaf, Blade - plus the places where user-facing text collects:
- i18n resources (`assets/i18n/*.json`, `messages.xlf`, `messages*.properties`) - the fastest way to every string the persona will ever read
- validation and error messages, including the ones the backend hands through unchanged
- empty states, loading states, disabled buttons and their tooltips

A static review can judge wording, missing feedback and unexplained states. It cannot judge flow, timing or where the eye lands - say that in the report instead of pretending otherwise.

## 3 - Walk the task, in character

One step at a time, in the order the persona would take them. **No developer shortcuts**: no typing a deep URL, no DevTools, no keyboard shortcuts the persona doesn't have, no back button unless `patience` says they'd use it, no reading the code to find out where a button is. If you can't find the next step by looking at the page, that *is* the finding - record it and stop.

At every step, answer these four - the ones the walkthrough is actually made of:

1. **Goal** - does the persona know what to do next at this point, without being told?
2. **Visibility** - is the control they need actually in front of them, on their `device`, without scrolling for it or hovering to reveal it?
3. **Mapping** - would they recognise *this* control as the one leading to their goal? An icon without a label almost never passes here.
4. **Feedback** - after the click, do they know whether it worked, is still running, or failed - and what to do next?

Plus, at every step: does any word appear that `forbidden_vocabulary` bans, and would `patience` have them abort here? An abort ends the walkthrough. Don't push on "as a developer would" - note where they'd stop and what they'd do instead (call someone, close the tab, try the same button once more).

**Stay an observer, not an actor.** No first-person theatre, no "oh no, I'm confused". Findings, with evidence.

**Don't break anything.** The task may involve sending, paying, deleting or publishing. Ask before every step that leaves the system or destroys data, and make test data recognisable as such (`Testrechnung Persona-Review`). If I say no, note the step as unverified rather than skipping it silently.

**Don't get stuck.** Element doesn't respond, page won't load, same error twice: stop, report what you have so far, ask how to continue. No third attempt.

## 4 - Write the report

To `.claude/personas/reviews/YYYY-MM-DD-<persona>-<task-slug>.md`, creating the folder if needed. In the language of the persona file - the findings quote the UI, and a translated quote is useless.

Before writing, look for older reports for the same persona and task in that folder and read the most recent one - match on the `task` in their frontmatter, not on the filename. If there is one, the report gets a **Seit dem letzten Review** section: what's fixed, what's still open, what's new. That comparison is the reason these files are dated.

Structure - `examples/report.md` next to this file shows the whole thing:

- **Frontmatter**: `persona`, `task`, `date`, `mode: browser | static`, `url` or the reviewed paths
- **Verlauf** - the steps, one line each, ending in where it worked out or where they stopped
- **Befunde** - numbered, blocking ones first. Each one:
  - **Fundstelle** - screen and the exact visible text, plus `file:line` when you have it. A finding without a location is not a finding
  - **Was verwirrt** - one or two sentences, tied to the persona file, not to general UX rules
  - **Schweregrad** - see below
  - **Vorschlag** - the concrete replacement text or the concrete change. Not "improve the wording" - write the sentence you'd put there
- **Nicht geprüft** - steps that were skipped, blocked or out of reach in static mode. One line each, or drop the section
- the closing note, verbatim, always:

  > Diese Befunde ersetzen keinen echten Nutzertest - bitte stichprobenhaft mit echten Personen abgleichen.

**Severity, so the levels stay comparable across reports:**
- **blockierend** - the persona doesn't get through here, or does something wrong with confidence. The task failed
- **störend** - they get through, but by guessing, backtracking, or without knowing whether it worked
- **kosmetisch** - they understand it, it's just wrong wording, inconsistent, or unnecessarily formal

**Quote, don't paraphrase.** Every finding carries the UI text verbatim. That's what makes two reports diffable and what lets me search for the string.

Then, in the chat: the count per severity, the one finding I should fix first, and the report path. Nothing else - the report has the detail.
