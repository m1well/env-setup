# m1well env-setup

This is just a collection of my public dotfiles and other stuff to setup an environment.
This repository is "under construction".

## usage

#### install m1well-toolsuite

To set up the m1well-toolsuite, just create a folder for the toolsuite and clone this repo into it.
Then cd into the env-setup folder and execute the [m1well-toolsuite.sh](/m1well-toolsuite.sh) file,
for example `bash m1well-toolsuite.sh -i`, and follow the instructions. The script then does all for you.

If you want vim and zsh styling, these tools have to be installed on your system.
At the end you just have to source your `.zshrc` or `.bashrc` file.

#### update m1well-toolsuite

Execute the following statement in the env-setup folder to update all repos in the m1well-toolsuite:
`bash m1well-toolsuite.sh -u` (all apps/repos have to stay on the master branch).

#### test m1well-toolsuite

Just build the Dockerfile and run the container. In the container then execute `bash m1well-toolsuite.sh -i`.

#### test m1well-toolsuite (legacy)

To run some tests just execute the following statement in the root folder: `bash test/m1well-test.sh`.

## explanation of the files

#### .cheatsheet ([link](/dotfiles/.cheatsheet))

This is the dotfile of my own written cheatsheet tool.
Source: [cheatsheet](https://github.com/m1well/cheatsheet)

#### .m1well_cli_master ([link](/dotfiles/.m1well_cli_master))

This file is my connection between the rc file and the files in the cli folder.

#### .vimrc ([link](/dotfiles/.vimrc))

This is my actual config file for vim.

#### .gitconfig.local.example ([link](/dotfiles/.gitconfig.local.example))

Template for machine-local, per-repo git identities. Copy it to `~/.gitconfig.local`
(without the `.example` suffix) and point it at your work repos to get a separate
name/email there. This is handled natively via git's `includeIf`, so the tracked
`.gitconfig` stays neutral and no private paths or company names end up in this repo.

#### .cli_base ([link](/cli/.cli_base))

This is my actual file for base aliases.

#### .cli_dev_tools ([link](/cli/.cli_dev_tools))

This is my actual file for dev tool aliases (like git, gradle, docker, ...).

#### .cli_functions ([link](/cli/.cli_functions))

This is my actual file for some useful functions.

#### .cli_m1well_toolsuite ([link](/cli/.cli_m1well_toolsuite))

This is my actual file for aliases regarding my own written toolsuite. Sources:

- [cheatsheet](https://github.com/m1well/cheatsheet)
- [versions](https://github.com/m1well/versions)
- [randomizer](https://github.com/m1well/randomizer)

It also (re)creates all the dotfile symlinks on every shell start, so they always point to the
current toolsuite files.

#### .cli_private ([link](/templates/.cli_private)) and .cli_projects ([link](/templates/.cli_projects))

These files are e.g. for your private exports / aliases / symlinks / functions / etc.
And you can additionally separate some working aliases etc. in the projects file.
During installation they are copied from the templates to the cli folder.

The advantage of these two files is that they aren't tracked via git (see [.gitignore](.gitignore)),
so they stay forever because they aren't affected by a toolsuite update.

#### .rc_template ([link](/templates/.rc_template))

This is the skeleton for the generated `.zshrc` / `.bashrc`.
During installation the placeholders (toolsuite home, iterm2 usage) get replaced
and the existing rc file is appended below it.

#### m1well.zsh-theme ([link](/terminal/m1well.zsh-theme))

This is my actual zsh theme.
If you want another username or hostname, just add the following statement to your `.cli_private` file
(just change the names) and source your rc file again:
`export ZSH_USER_PROMPT="my-name@my-hostname";`

#### m1well.plist ([link](/terminal/m1well.plist)) / m1well-16.plist ([link](/terminal/m1well-16.plist))

These are my actual iterm2 profiles - identical except for the window size:
`m1well` (57x205) and `m1well 16` (70x225) for the 16 inch machine.
Both get symlinked into the iterm2 `DynamicProfiles` folder, so both show up in the profile list
and you pick the one you want per machine via `Profiles > Other Actions > Set as Default`.
iterm2 stores that choice by guid in its app prefs, so it survives a reinstall of the symlinks -
but it also means the guids in these files must stay stable.
The matching nerd font (needed for the special zsh characters) is installed via homebrew:
`brew install --cask font-inconsolata-nerd-font`

#### init.lua ([link](/nvim/init.lua))

This is my actual neovim config (lazy.nvim, catppuccin, some key mappings).
It gets symlinked to `~/.config/nvim/init.lua`.

#### claude-code ([link](/claude-code))

My global [Claude Code](https://claude.com/claude-code) setup, symlinked into `~/.claude`:
`settings.json` (permissions, model, hooks, statusline), `statusline.sh` (custom status line),
`CLAUDE.md` (personal context), `rules/` (topic- and path-scoped instructions),
`skills/` (custom skills), `agents/` (subagents with their own role and tools)
and `hooks/` (shell scripts on lifecycle events).

`rules/` keeps `CLAUDE.md` short: `code-comments.md` only loads when a code file is
touched, the other two load every session. `hooks/` enforces what instructions only
suggest - a sound on stop and notification, `git add -A` after every turn,
a confirmation prompt before Claude reads a markdown file that neither I nor a
`CLAUDE.md` pointed it at (`CLAUDE_MD_GUARD=off` disables it), and one forced
cleanup plus docs question before Claude calls a task done, but only for turns
that added 15 lines or more (`CLAUDE_SESSION_REVIEW_MIN` moves that line,
`CLAUDE_SESSION_REVIEW=off` disables the check). That cleanup step gets a list from
`unused-imports.sh`, which flags imports in changed Kotlin, Java and TypeScript
files whose symbol appears nowhere else - candidates to check, not to delete
blindly, since an extension function or a decorator is used without naming it.

`agents/` holds two roles that pay off through context isolation: `mw-architect`
reads a lot and answers with an assessment (read-only tools), `mw-test-engineer`
writes tests and reports only the failures. Both inherit `CLAUDE.md` and `rules/`.

Two of those skills live in their own public repo, [topomap-skills](https://github.com/m1well/topomap-skills),
and are symlinked into `skills/` from there. The install script clones it next to this
one; without that repo the two links dangle.

`mw-persona-review` walks the running app through the eyes of a persona with low tech literacy:
`/mw-persona-review persona=julia task="Lege eine Rechnung über 250€ an und sende sie per E-Mail"`.
It drives the app in Chrome via the Claude Code Chrome extension - the extension has to be installed
and the site allowed in its permissions, otherwise the skill falls back to a static review of the
frontend code and says so in the report. Personas live per project in `.claude/personas/*.md`,
reports land dated in `.claude/personas/reviews/` so runs can be compared over time. Two example
personas and a sample report in the skill's `examples/` folder show the format.

`mw-springboot` and `mw-angular` are the house rules for the two stacks I write most - they
apply when Claude writes code and when it reviews it. Backend: constructor injection and
one-way layering, DTOs at the HTTP boundary, transactions on the service, entity versus
embeddable, Flyway or Liquibase, default-deny security, the cheapest test slice. It stays
language- and build-agnostic, so the same rules hold for Kotlin or Java and Gradle or Maven.
Every rule has an id (`WEB-1`, `MODEL-7`, `MIG-2`), so a review finding points at one instead
of at an opinion, and the `examples/` folder carries a wrong/right pair for each in both
languages.

#### Brewfile ([link](/homebrew/Brewfile))

A declarative list of my most important CLI tools, casks and fonts.
Install everything with `brew bundle --file=homebrew/Brewfile` - it is idempotent,
so already installed formulae are skipped and it can be re-run any time.

## Copyright

Copyright :copyright: 2026 Michael Wellner ([@m1well](https://m1well.com))
