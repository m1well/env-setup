#!/bin/bash
###
#title                  :main.sh
#description            :This script provides an environment setup.
#author                 :Michael Wellner (@m1well) twitter.m1well.de
#date of creation       :20181210
#date of last change    :20181210
#version                :0.1.0
#usage                  :main.sh <path to user's home> <path to m1well-toolsuit's home>
#notes                  :
###

# debian / ubuntu
# run this commands:
# apt-get update && apt-get -y install build-essential curl file git
# mkdir m1well-toolsuite && cd m1well-toolsuite && git clone https://github.com/m1well/env-setup.git

##########
# UNDER CONSTRUCTION!!!!
##########

HOME_PATH=${1}
TOOLSUITE_PATH=${2}

### constants ###
BR="\n"
FONT_CYAN="\033[0;96m"
FONT_NONE="\033[0m"
TAB=24
HASHLINE="######################################################"
HEADER="################## m1well env-setup ##################"

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
isStringEqual() {
  if [ "${1}" == "${2}" ] ; then return 0 ; fi
  return 1
}
installVim() {
  apt-get -y install vim
}
installZsh() {
  apt-get -y install zsh && sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
}
installUuid() {
  apt-get install uuid-runtime
}
addTools() {
  git clone https://github.com/m1well/cheatsheet.git
  git clone https://github.com/m1well/versions.git
  git clone https://github.com/m1well/randomizer.git
  git clone https://github.com/m1well/bashlist.git
}
copyCliAliasPrivate() {
  cp ${TOOLSUITE_PATH}/env-setup/templates/.cli_aliases_private ${TOOLSUITE_PATH}/env-setup/dotfiles/.cli_aliases_private
}
switchShell() {
  chsh -s $(which zsh)
}
createZshrcFile() {
  local ESCAPED_HOME_PATH=$(echo "${HOME_PATH}" | sed 's/\//\\\//g')
  local ESCAPED_TOOLSUITE_PATH=$(echo "${TOOLSUITE_PATH}" | sed 's/\//\\\//g')
  cat ${TOOLSUITE_PATH}/env-setup/templates/.zshrc | sed -e "s/§§USER_HOME§§/${ESCAPED_HOME_PATH}/g" | sed -e "s/§§TOOLSUITE_HOME§§/${ESCAPED_TOOLSUITE_PATH}/g" > ${HOME_PATH}/.zshrc
  source ${HOME_PATH}/.zshrc
}

printStartLines
if isStringEqual "${HOME_PATH}" "" ; then
  echo "No path to user home set"
else
  cd ${TOOLSUITE_PATH}
  installVim
  installZsh
  installUuid
  addTools
  copyCliAliasPrivate
  switchShell
  # createZshrcFile
fi
printEndLines

### end of script ###

#####################
