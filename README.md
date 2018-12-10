# m1well env-setup

This is just a collection of my public dotfiles and other stuff to setup an environment.<br>
This repository is "under construction".<br>

## usage
#### install m1well-toolsuite
To set up the m1well-toolsuite, just execute the [m1well-toolsuite.sh](/m1well-toolsuite.sh) <br>
file - for example: `bash m1well-toolsuite.sh`<br>
The script does all for you.<br>

#### setup .zshrc or .bash_profile
To startup you have to add following snippet to your `.zshrc` file<br>
and please replace the words in brackets.<br>
```
export USER_HOME="{{USER_HOME}}";
export M1WELL_TOOLSUITE_HOME="{{TOOLSUITE_HOME}}";
export ZSH_USER_PROMPT="{{YOUR_USER_PROMPT}}";

. ${M1WELL_TOOLSUITE_HOME}/env-setup/dotfiles/.cli_aliases_base
. ${M1WELL_TOOLSUITE_HOME}/env-setup/dotfiles/.cli_aliases_dev_tools
. ${M1WELL_TOOLSUITE_HOME}/env-setup/dotfiles/.cli_functions_symlinks
. ${M1WELL_TOOLSUITE_HOME}/env-setup/dotfiles/.cli_aliases_m1well_toolsuite
. ${M1WELL_TOOLSUITE_HOME}/env-setup/dotfiles/.cli_aliases_private
```

## explanation of the files
#### .cheatsheet ([link](/dotfiles/.cheatsheet))
This is the dotfile of my own written cheatsheet tool.<br>
source: [cheatsheet](https://github.com/m1well/cheatsheet)<br>

#### .cli_aliases_base ([link](/dotfiles/.cli_aliases_base))
This is my actual file for base aliases.<br>

#### .cli_functions_symlinks ([link](/dotfiles/.cli_functions_symlinks))
This is my actual file for some useful functions and symlinks.<br>

#### .cli_aliases_dev_tools ([link](/dotfiles/.cli_aliases_dev_tools))
This is my actual file for dev tool aliase (like git, gradle, docker, ...).<br>

#### .cli_aliases_m1well_toolsuite ([link](/dotfiles/.cli_aliases_m1well_toolsuite))
This is my actual file for aliases regarding to my own written toolsuite.<br>
source: [cheatsheet](https://github.com/m1well/cheatsheet)<br>
source: [versions](https://github.com/m1well/versions)<br>
source: [randomizer](https://github.com/m1well/ranzomizer)<br>
source: [bashlist](https://github.com/m1well/bashlist)<br>

#### .vimrc ([link](/dotfiles/.vimrc))
This is my actual config file for vim.<br>

#### m1well.zsh-theme ([link](/terminal/m1well.zsh-theme))
This is my actual zsh theme.<br>

## Copyright
Copyright :copyright: 2018 Michael Wellner ([@m1well](http://www.twitter.m1well.de))<br>
