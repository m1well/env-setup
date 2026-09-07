---
name: mw-analyze-class
description: Summarizes one class - what it is, what it depends on, what it offers - in the vocabulary of the house rules, so a Kotlin service reads as a stereotype and an Angular component reads as a layer. Invoked via /mw-analyze-class.
disable-model-invocation: true
argument-hint: <class-name-or-path>
---

# Analyze class

Read the class named in `$ARGUMENTS` - search the project for it if it is a name
rather than a path. Several matches: list them one line each and ask, don't summarize
all of them.

This is a summary, not a review and not a trace. Related: `/mw-springboot` and
`/mw-angular` review against the rules, `/mw-trace` follows one thing across classes.

Always open with:

**Summary** - 2-3 sentences: what the class does and what it is there for. Then the
sections for its kind.

## Kotlin or Java

**Stereotype** - `@Service`, `@Repository`, `@RestController`, `@Configuration`,
`@Entity`, `@Embeddable`, or "none, it is a plain class". A `@Component` that is
really one of the others is worth a word (STR-2).

**Injected** - constructor dependencies, type and name, one per line. "none" if there
are none. Field injection gets named as what it is (STR-1).

**Static** - constants, companion members, static methods. "none" if there are none.

**Functions** - public methods with their signature and half a line on what each
does. Skip pure getters and setters. On an entity, say which methods carry behaviour
and which are plain accessors (MODEL-11).

**Persistence** *(entity or embeddable only)* - table name, columns with types, the
key, and the associations with their fetch type.

## Angular

Work out the layer first - **atom, molecule, organism, template, page**, or for an
`@Injectable` whether it is **state** or **api**. The file path usually says it; the
domain types in the signature decide it when the path does not.

**Component**

- **Layer** - which one, and the one fact that makes it that one
- **Inputs / outputs** - `input()`, `input.required()`, `output()`, `model()` with
  their types, one per line. A component still on `@Input()` / `@Output()` gets that
  noted once - the decorators are out under the house rules (SIG-1)
- **Injected** - what `inject()` returns, one per line. "none" is the expected answer
  below the page layer (LAYER-7)
- **State** - the component's own signals: `signal`, `computed`, `linkedSignal`,
  `viewChild`. Say which are writable
- **Functions** - public and protected methods, one line each
- **Template** - 3-5 bullets on what the markup renders: structure, control flow,
  where the inputs land. Not a line-by-line translation

**Service**

- **Kind** - state service or api service
- **Injected** - one per line
- **Exposed** - the readonly surface: `computed`, `.asReadonly()`, and every
  `httpResource` / `rxResource` with what it fetches and what makes it reload
- **Private state** - the writable signals behind it, one per line
- **Commands** - the methods that mutate, named after what they do

## Rules

Bullets only, no prose beyond the summary. A section with nothing in it says "none"
rather than disappearing - that the list is empty is itself the finding.

Rule IDs (`STR-2`, `MODEL-11` on the backend, `SIG-1`, `LAYER-7` on the frontend)
are pointers, not a review. At most one closing line if something stood out, then
name the skill that would look at it properly.
