---
paths:
  - "**/*.{kt,java,ts,tsx,js,html,css,scss,sql,sh,bash,zsh,yaml,yml,gradle,kts}"
---

# Code comments

Default is no comment. Write one only when all three hold:
- the *why* is not derivable from the code, the names or the test
- a reader would otherwise get it wrong (a workaround, a spec quirk, an ordering constraint, a deliberate deviation)
- it stays one line

Never write:
- a comment restating what the next line does (`// increment counter`, `// inject the repo`)
- section banners (`// ---- helpers ----`), block headers above obvious groups
- KDoc/JSDoc/Javadoc on anything whose signature already says it - public API only, and only when it carries a constraint or a unit
- `TODO` / `FIXME` unless I asked for it
- comments in tests - the test method name carries the meaning
- a comment describing the change you just made ("now uses X instead of Y") - that belongs in the chat, not in the file

When editing existing code: leave foreign comments alone unless they became wrong. Delete comments that your change made stale.

If you feel the urge to explain a block, extract it into a named function instead.
