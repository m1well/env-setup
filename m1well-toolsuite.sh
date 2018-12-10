#!/bin/bash
###
#title                  :m1well-toolsuite.sh
#description            :This script provides an environment setup.
#author                 :Michael Wellner (@m1well) twitter.m1well.de
#date of creation       :20181210
#date of last change    :20181210
#version                :0.1.0
#usage                  :m1well-toolsuite.sh
#notes                  :
###

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
installTools() {
  git clone https://github.com/m1well/cheatsheet.git
  git clone https://github.com/m1well/versions.git
  git clone https://github.com/m1well/randomizer.git
  git clone https://github.com/m1well/bashlist.git
}
copyCliAliasPrivate() {
  cp env-setup/templates/.cli_aliases_private env-setup/dotfiles/.cli_aliases_private
}

printStartLines

cd ..
installTools
copyCliAliasPrivate

printEndLines

### end of script ###

#####################
