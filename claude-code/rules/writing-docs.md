# Writing markdown docs

Applies to every `.md` file you write or edit - READMEs, ADRs, guides, notes.

**Budget first.** Say the number of lines you plan before writing, then stay under it. A README section is 3-8 lines. A new doc that needs more than 60 lines is a sign the topic should be split or dropped.

**Be specific, not complete.** One concrete fact beats three general sentences. Write the exact command, the exact path, the exact value:
- "Run `./gradlew :api:test --tests '*OrderService*'`" not "run the relevant tests"
- "Config lives in `src/main/resources/application.yml`" not "configuration is externalized"

**Cut on sight:**
- anything derivable from the code, the file tree or `--help`
- intros, "Overview", "Introduction", closing summaries, "Conclusion"
- restating the heading in the first sentence
- lists of obvious prerequisites (Java, Docker, git)
- adjectives that carry no fact - robust, powerful, seamless, comprehensive
- a table with two columns and two rows - use a sentence

**Shape:** short headings, bullets over paragraphs, code blocks over prose describing code. Prose only where a bullet would lose the reasoning.

**Editing an existing doc:** patch the lines that are wrong, keep the file's voice and structure. Do not restructure or "improve" sections nobody asked about, and do not append a changelog entry unless the file already has one.
