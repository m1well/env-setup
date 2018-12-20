# m1well env-setup

This is just a collection of my public dotfiles and other stuff to setup an environment.<br>
This repository is "under construction".<br>

## usage
#### install m1well-toolsuite
To set up the m1well-toolsuite, just  create a folder for the toolsuite and clone this repo in it. <br>
then cd into the env-setup folder and just execute the [m1well-toolsuite.sh](/m1well-toolsuite.sh) file<br>
for example: `bash m1well-toolsuite.sh -i` and follow the instructions.<br>
The script then does all for you.<br>
If you want vim and zsh styling - these tools have to be installed on your system.<br>
At the end you just have to source your `.zshrc` or `.bashrc`. file. <br>

#### update m1well-toolsuite
Execute following statement in the env-setup folder to update all repos<br>
in the m1well-toolsuite: `bash m1well-toolsuite.sh -u` <br>
(All apps/repos have to stay in the master branch!) <br>

#### test m1well-toolsuite
To run some test just execute following statement in the rootfolder: <br>
`bash test/m1well-test.sh` <br>

## explanation of the files
#### .cheatsheet ([link](/dotfiles/.cheatsheet))
This is the dotfile of my own written cheatsheet tool.<br>
source: [cheatsheet](https://github.com/m1well/cheatsheet)<br>

#### .m1well_cli_master ([link](/dotfiles/.m1well_cli_master))
This file is my connection between the rc file and the files in the cli folder.<br>

#### .vimrc ([link](/dotfiles/.vimrc))
This is my actual config file for vim.<br>

#### .cli_base ([link](/cli/.cli_base))
This is my actual file for base aliases.<br>

#### .cli_dev_tools ([link](/cli/.cli_dev_tools))
This is my actual file for dev tool aliase (like git, gradle, docker, ...).<br>

#### .cli_functions ([link](/cli/.cli_functions))
This is my actual file for some useful functions.<br>

#### .cli_m1well_toolsuite ([link](/cli/.cli_m1well_toolsuite))
This is my actual file for aliases regarding to my own written toolsuite.<br>
source: [cheatsheet](https://github.com/m1well/cheatsheet)<br>
source: [versions](https://github.com/m1well/versions)<br>
source: [randomizer](https://github.com/m1well/ranzomizer)<br>
source: [bashlist](https://github.com/m1well/bashlist)<br>

#### .cli_private ([link](/templates/.cli_private)) and cli_projects ([link](/templates/.cli_projects))
These files are e.g. for your private exports / aliases / symlinks / functions / etc.<br>
And you can additionally seperate some working aliases etc in the projects file.<br>
During installation, they are getting copied from the templates to the dotfiles folder.<br>
The advantage of these two files is, they aren't tracked via git (see ([.gitignore](.gitignore))) <br>
so they stay forever because they aren't affected on a toolsuite update.<br>

#### m1well.zsh-theme ([link](/terminal/m1well.zsh-theme))
This is my actual zsh theme.<br>
If you want another username or hostname just add following statement to your `.cli_private` file:<br>
`export ZSH_USER_PROMPT="my-name@my-hostname";` (just change the names)<br>
Then source again your rc file.<br>

## Copyright
Copyright :copyright: 2018 Michael Wellner ([@m1well](http://www.twitter.m1well.de))<br>
