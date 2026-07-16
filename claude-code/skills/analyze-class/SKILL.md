---
description: Analyzes a class and summarizes it, adapting the format to whether it's a Kotlin/Java class, an Angular component, or an Angular service
argument-hint: <class-name-or-path>
---

Find and read the class referenced in $ARGUMENTS. If it's a class name
rather than a path, search the project for it.

Always start with:

**Summary**
- 2-3 sentences on what the class does and its role in the system.

Then continue depending on what kind of class it is:

**If it's a Kotlin or Java class:**

**Injected**
- Constructor-injected dependencies (type + name), one per line.
  Write "none" if there are none.

**Static**
- Static fields, constants, companion-object members, or static methods,
  one per line. Write "none" if there are none.

**Functions**
- Public methods with their signature (name, parameters, return type),
  one per line. Skip trivial getters/setters unless they contain logic.

**If it's an Angular component:**

**Declarations**
- `@Input()` / `@Output()` properties (or signal-based `input()`/`output()`),
  one per line with type
- Injected dependencies (constructor or `inject()`), one per line

**Functions**
- Public methods, one per line with a short explanation of what each does

**Template**
- 3-5 bullet points on what the HTML template renders: structure, key
  bindings, notable directives. Not a line-by-line translation.

**If it's an Angular service:**

Same as component (**Declarations** + **Functions**), but skip the
**Template** section entirely - services have no template.

Keep everything terse: bullet points only, no prose beyond the initial
2-3 sentence summary.

