#!/bin/bash
###
#title                  : m1well-toolsuite.sh
#description            : This script provides a setup for the m1well-toolsuite.
#author                 : Michael Wellner (@m1well) twitter.m1well.de
#date of creation       : 20181210
#date of last change    : 20250506
#version                : 2.0.0
#usage                  : m1well-toolsuite.sh [-i|-u]
#notes                  : prerequisits
#                       : debian / ubuntu (e.g. a docker container) -- run this to get git: "apt-get update && apt-get -y install git vim"
#                       : osx with homebrew -- run: "brew update && brew install git"
#                       : for vim and zsh styling - you need vim and zsh installed
#                       : to run this script you have to do following steps (wherever you want):
#                       : execute "mkdir m1well-toolsuite && cd m1well-toolsuite && git clone https://github.com/m1well/env-setup.git && cd env-setup"
###

set -eu

### constants ###
BR="\n"
FONT_CYAN="\033[0;96m"
FONT_GREEN="\033[0;92m"
FONT_NONE="\033[0m"
HASHLINE="######################################################"
HEADER="################## m1well toolsuite ##################"

printStartLines() {
  printf "${FONT_CYAN}"
  printf "${HASHLINE}${BR}"
  printf "${HEADER}${BR}"
  printf "${HASHLINE}${BR}"
  printf "${FONT_NONE}"
}
printEndLines() {
  printf "${FONT_CYAN}"
  printf "${HASHLINE}${BR}"
  printf "${FONT_NONE}"
}
printSuccess() {
  if [ -f ${HOME}/.zshrc ]; then
    local file=${HOME}/.zshrc
  else
    local file=${HOME}/.bashrc
  fi
  printf "${FONT_GREEN}"
  printf "##### succeeded ${BR}"
  printf "##### if you added the iterm2 profile file you have to set it as default profile ${BR}"
  printf "##### now you have to source your rc file to finish: ${BR}"
  printf "##### \"source ${file}\" ${BR}"
  printf "${FONT_NONE}"
}
printUsage() {
  echo "Invalid option - you can only use -i for installation or -u for update" >&2
}
isStringEqual() {
  if [ "${1}" == "${2}" ] ; then return 0 ; fi
  return 1
}
installTools() {
  cd ..
  if [ -d cheatsheet ]; then
    printf "## cheatsheet project apparently already exists ${BR}"
  else
    git clone https://github.com/m1well/cheatsheet.git
  fi
  if [ -d versions ]; then
    printf "## versions project apparently already exists ${BR}"
  else
    git clone https://github.com/m1well/versions.git
  fi
  if [ -d randomizer ]; then
    printf "## randomizer project apparently already exists ${BR}"
  else
    git clone https://github.com/m1well/randomizer.git
  fi  
}
copyCliMaster() {
  cp dotfiles/.m1well_cli_master ${HOME}/.m1well_cli_master
}
copyIndividualCliFiles() {
  cp templates/.cli_private cli/.cli_private
  cp templates/.cli_projects cli/.cli_projects
}
commentOutLine() {
  if [[ "${OSTYPE}" == darwin* ]]; then
    sed -i -temp -e "/${2}/s/^/# /g" ${1}
    rm ${1}-temp
  else
    sed -e "/${2}/s/^/# /g" ${1} > ${1}-temp
    mv ${1}-temp ${1}
  fi
}
replaceString() {
  if [[ "${OSTYPE}" == darwin* ]]; then
    sed -i -temp -e "s|${2}|${3}|g" ${1}
    rm ${1}-temp
  else
    sed -e "s|${2}|${3}|g" ${1} > ${1}-temp
    mv ${1}-temp ${1}
  fi
}
generateRcFile() {
  cp ${RC_TEMPLATE_FILE} ${RC_TEMPLATE_FILE}.copy
  replaceString ${RC_TEMPLATE_FILE}.copy "&&userhome&&" "${HOME}"
  replaceString ${RC_TEMPLATE_FILE}.copy "&&toolsuitehome&&" "${TOOLSUITE_HOME}"
  replaceString ${RC_TEMPLATE_FILE}.copy "&&gitname&&" "${GIT_USER_NAME}"
  replaceString ${RC_TEMPLATE_FILE}.copy "&&gitemail&&" "${GIT_USER_EMAIL}"
  if [ -e "${HOME}/${RC_FILE}" ]; then
    cat ${HOME}/${RC_FILE} >> ${RC_TEMPLATE_FILE}.copy
  fi
  mv ${RC_TEMPLATE_FILE}.copy ${HOME}/${RC_FILE}
}
disableVim() {
  commentOutLine cli/.cli_private ".vimrc"
  git config --global --unset core.editor
}
disableIterm2Profile() {
  USE_FONT=false
  commentOutLine cli/.cli_private "m1well.plist"
}
copyFontIfNeeded() {
  if [ "${USE_FONT}" = true ]; then
    cp terminal/font/Inconsolata\ Nerd\ Font\ Complete\ Mono.otf ${HOME}/Library/Fonts/Inconsolata\ Nerd\ Font\ Complete\ Mono.otf
  fi
}
disableZsh() {
  commentOutLine cli/.cli_private "m1well.zsh-theme"
  RC_FILE=".bashrc" # if no zsh - then bashrc
}
createSshConfig() {
  mkdir -p ${HOME}/.ssh
  ssh-keygen -t rsa -b 4096 -f ${HOME}/.ssh/github-ssh.id_rsa -C "${GIT_USER_EMAIL}"
  if (( $EUID != 0 )); then
    sudo sh -c 'echo "\n# defaults\nHost *\n  AddressFamily inet\n  Protocol 2\n  Compression yes\n  ServerAliveInterval 60\n\n# github ssh\nHost github.com\n  HostName github.com\n  User git\n  IdentityFile ${HOME}/.ssh/github-ssh.id_rsa"' >> ${HOME}/.ssh/config
  else
    sh -c 'echo "\n# defaults\nHost *\n  AddressFamily inet\n  Protocol 2\n  Compression yes\n  ServerAliveInterval 60\n\n# github ssh\nHost github.com\n  HostName github.com\n  User git\n  IdentityFile ${HOME}/.ssh/github-ssh.id_rsa"' >> ${HOME}/.ssh/config
  fi
  printf "copy following public key to your github account and then change your remotes from https url to ssh url: ${BR}${BR}"
  cat ${HOME}/.ssh/github-ssh.id_rsa.pub
  printf "${BR}${BR}"
}
askQuestion() {
  read -n1 -p "${1} (y/n)? "
  echo ""
}
installation() {
  TEMP_FILE=".temp"
  RC_FILE=".zshrc"
  RC_TEMPLATE_FILE="templates/.rc_template"
  GITCONFIG_FILE="dotfiles/.gitconfig"
  TOOLSUITE_HOME=$(cd .. && pwd)
  USE_FONT=true
  copyCliMaster
  copyIndividualCliFiles
  read -p "git user name: " GIT_USER_NAME
  read -p "git user email: " GIT_USER_EMAIL
  askQuestion "vim already installed?"
  [[ ! $REPLY =~ ^[Yy]$ ]] && disableVim
  askQuestion "iterm2 installed and want to use m1well profile?"
  [[ ! $REPLY =~ ^[Yy]$ ]] && disableIterm2Profile
  copyFontIfNeeded
  askQuestion "zsh already installed?"
  [[ ! $REPLY =~ ^[Yy]$ ]] && disableZsh
  askQuestion "generate ssh config and ssh key for github?"
  [[ $REPLY =~ ^[Yy]$ ]] && createSshConfig
  generateRcFile
  mkdir -p ${HOME}/.config/nvim
  installTools
}
update() {
  cd ..
  for dir in ${M1WELL_TOOLSUITE_HOME}/*; do
    if [ -d "${dir}" ]; then
      cd ${dir}
      git pull origin master
      cd ..
    fi
  done
}

### start of script ###

printStartLines

while getopts ":iuh" opt; do
  case $opt in
    i)
      echo "installation (OSTYPE: ${OSTYPE})"
      installation
      printSuccess
      ;;
    u)
      echo "update (OSTYPE: ${OSTYPE})"
      update
      printSuccess
      ;;
    h | *)
      printUsage
      ;;
  esac
done
cd ..

printEndLines

### end of script ###

#####################
