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

#### .cli_private ([link](/templates/.cli_private)) and .cli_projects ([link](/templates/.cli_projects))

These files are e.g. for your private exports / aliases / symlinks / functions / etc.
And you can additionally separate some working aliases etc. in the projects file.
During installation they are copied from the templates to the cli folder.

The advantage of these two files is that they aren't tracked via git (see [.gitignore](.gitignore)),
so they stay forever because they aren't affected by a toolsuite update.

#### .rc_template ([link](/templates/.rc_template))

This is the skeleton for the generated `.zshrc` / `.bashrc`.
During installation the placeholders (toolsuite home, git user/email) get replaced
and the existing rc file is appended below it.

#### m1well.zsh-theme ([link](/terminal/m1well.zsh-theme))

This is my actual zsh theme.
If you want another username or hostname, just add the following statement to your `.cli_private` file
(just change the names) and source your rc file again:
`export ZSH_USER_PROMPT="my-name@my-hostname";`

#### m1well.plist ([link](/terminal/m1well.plist))

This is my actual iterm2 profile.
If you want, the installation process copies it to the right folder and then you can set it as default profile.
The matching nerd font (needed for the special zsh characters) is installed via homebrew:
`brew install --cask font-inconsolata-nerd-font`

#### init.lua ([link](/nvim/init.lua))

This is my actual neovim config (lazy.nvim, catppuccin, some key mappings).
It gets symlinked to `~/.config/nvim/init.lua`.

#### claude-code ([link](/claude-code))

My global [Claude Code](https://claude.com/claude-code) setup, symlinked into `~/.claude`:
`settings.json` (permissions, model, statusline), `statusline.sh` (custom status line),
`CLAUDE.md` (personal context) and `skills/` (custom skills).

#### Brewfile ([link](/homebrew/Brewfile))

A declarative list of my most important CLI tools, casks and fonts.
Install everything with `brew bundle --file=homebrew/Brewfile` - it is idempotent,
so already installed formulae are skipped and it can be re-run any time.

## Copyright

Copyright :copyright: 2026 Michael Wellner ([@m1well](https://m1well.com))
