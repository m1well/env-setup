---
name: trace
description: Follows one thing through the system — a request, a value, an event, a prop — station by station, naming the mechanism behind every hop and flagging where the thread breaks. Invoked via /trace.
disable-model-invocation: true
argument-hint: <what to follow — endpoint, value, event, function> [· "back" to follow it upstream]
---

# Trace

Follow *one* thing through the system and show me the chain — where it enters, which stations it passes, what it turns into, and where it leaves. I want the path, not an architecture lecture.

**What to follow** comes from `$ARGUMENTS`: an endpoint, a function, a value or field, an event or message type, a component input, a config property. If it's ambiguous — the name exists in several places — list the candidates in one line each and ask which one before tracing. Don't trace all of them.

**Direction.** Default is forward: from the thing, downstream, until it leaves the system. If `$ARGUMENTS` contains `back` (or the phrasing is clearly "where does this come from"), go upstream instead — from the thing to its origin. Say which direction you took in the answer.

## Follow the transitions, not the technology

Every hop is one of these. Name the mechanism, because it tells you *how* to find the next station — that's the whole job:

- **Call** — one function invokes the next. The default hop. Follow the callee into its definition.
- **Injection** — the declared type is an interface or abstract class; the real work lives in an implementation. Search for implementations of that type. More than one? Say so, then pick the one actually wired up in this context.
- **Binding** — markup wires a parent to a child (component inputs/outputs, props, template includes, slots). The hop is *in the template, not in the code file* — grep the templates for the child's selector or tag to find who passes what.
- **Event / message** — publisher and subscriber are not connected by a call. The link is a name or a type: grep for the event type, topic, or channel and list every consumer you find.
- **Configuration** — a route table, annotation, or config file maps a key to a handler: URL to method, queue to listener, key to bean. The next station is named in config, not in code.
- **Boundary** — it leaves the process: HTTP client, database, queue publish, file, external API. The trace ends here. Name what crosses the boundary and where it presumably lands — don't guess at the other side's internals.

## Stay on the main path

A trace is a chain, not a tree. Follow the one path the thing actually takes. Everything else — logging, validation, mapping helpers, error branches, metrics — gets at most a one-line mention under side branches, never its own hop. If a station genuinely forks into two equal paths, say so and ask which one to follow rather than tracing both.

**Stop** at a process boundary, at a station that only stores or returns, when the path loops back to something already listed (say "cycle"), or after roughly 10 hops — if it's longer than that, report what you have and offer to continue from the last station.

**Read the code, don't infer it.** Every station needs a real `file:line` you actually opened. If you can't find the next hop, say where the trail went cold and why — a guessed station is worse than a short chain.

## Answer with

- **Following** — one line: what you traced, in which direction.
- **The chain** — numbered stations, one block each:
  `file:line` — what happens here, in half a sentence
  then the transition to the next station in brackets, e.g. `[binding → user-card.html:14]`
- **What changes on the way** — every rename and reshape: `currentUser` → `user` → `data`, DTO → entity → row. Only the hops where it actually changes. This is usually the part I couldn't see myself, so don't skip it.
- **Where it gets fuzzy** — the weak links: several implementations behind one interface, multiple subscribers on one event, reflection or string-keyed lookup, a type that loses information (`any`, raw map, untyped JSON). Write "nothing" if the path is tight.
- **Side branches** — one line each, not followed. Skip the section if there are none.
- **Assessment** — 2-3 sentences: what this chain is evidently there to do, and how it was built — the pattern behind it, whether the layering holds up, what the design seems to optimise for. Then **one** thing worth improving, and only one.

**The assessment comes last, and only when the chain is actually finished** — it reached a boundary or a final station. A chain cut short by the hop limit, a cold trail, or an open fan-out question doesn't get one: judging half a path is worse than not judging it.

The improvement must follow from what you read, not from general best practice — the strongest ones usually come straight out of the fuzzy spots or the renames you already listed. No rewrites, no new layer or abstraction, nothing that needs a redesign to be worth doing. And if the chain is genuinely well built, say that plainly instead of inventing a weakness.

Keep it terse — no prose beyond the half-sentence per station and the assessment at the end.
