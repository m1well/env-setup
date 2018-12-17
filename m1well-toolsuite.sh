#!/bin/bash
###
#title                  : m1well-toolsuite.sh
#description            : This script provides an environment setup.
#author                 : Michael Wellner (@m1well) twitter.m1well.de
#date of creation       : 20181210
#date of last change    : 20181217
#version                : 1.2.0
#usage                  : m1well-toolsuite.sh [-i|-u]
#notes                  : prerequisits
#                       : debian / ubuntu (e.g. a docker container) -- run this to get git: "apt-get update && apt-get -y install git"
#                       : osx with homebrew -- run: "brew update && brew install git"
#                       : for vim and zsh styling - you need vim and zsh installed
#                       : to run this script you have to do following steps (wherever you want):
#                       : execute "mkdir m1well-toolsuite && cd m1well-toolsuite && git clone https://github.com/m1well/env-setup.git && cd env-setup"
###

### constants ###
BR="\n"
FONT_CYAN="\033[0;96m"
FONT_GREEN="\033[0;92m"
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
printUsage() {
  echo "Invalid option - you can only use -i for installation or -u for update" >&2
}
isStringEqual() {
  if [ "${1}" == "${2}" ] ; then return 0 ; fi
  return 1
}
installTools() {
  cd ..
  git clone https://github.com/m1well/cheatsheet.git
  git clone https://github.com/m1well/versions.git
  git clone https://github.com/m1well/randomizer.git
  git clone https://github.com/m1well/bashlist.git
}
copyIndividualCliFiles() {
  cp templates/.cli_private dotfiles/.cli_private
  cp templates/.cli_projects dotfiles/.cli_projects
}
generateRcFile() {
  sed -i .original -e "s|&&userhome&&|${USER_HOME}|g" ${RC_TEMPLATE_FILE}
  sed -i .temp -e "s|&&toolsuitehome&&|${TOOLSUITE_HOME}|g" ${RC_TEMPLATE_FILE}
  sed -i .temp -e "s|&&gitname&&|${GIT_USER_NAME}|g" ${RC_TEMPLATE_FILE}
  sed -i .temp -e "s|&&gitemail&&|${GIT_USER_EMAIL}|g" ${RC_TEMPLATE_FILE}
  cat ${USER_HOME}/${RC_FILE} >> ${RC_TEMPLATE_FILE}
  mv ${RC_TEMPLATE_FILE} ${USER_HOME}/${RC_FILE}
  mv ${RC_TEMPLATE_FILE}.original ${RC_TEMPLATE_FILE}
  rm templates/.rc_template.temp
}
disableVim() {
  sed '/.vimrc/s/^/# /g' -i dotfiles/.cli_private
}
disableZsh() {
  sed '/m1well.zsh-theme/s/^/# /g' -i dotfiles/.cli_private
  RC_FILE=".bashrc" # if no zsh - then bashrc
}
installation() {
  TEMP_FILE=".temp"
  RC_FILE=".zshrc"
  RC_TEMPLATE_FILE="templates/.rc_template"
  USER_HOME=${HOME}
  TOOLSUITE_HOME=$(cd .. && pwd)
  copyIndividualCliFiles
  read -p "git user name: " GIT_USER_NAME
  read -p "git user email: " GIT_USER_EMAIL
  read -n1 -p "vim already installed?? (y/n)? "
  [ "$REPLY" != "y" ] && disableVim
  echo ""
  read -n1 -p "zsh already installed?? (y/n)? "
  [ "$REPLY" != "y" ] && disableZsh
  echo ""
  generateRcFile
  installTools
}
success() {
  printf "${FONT_GREEN}"
  printf "##### now you have to source your rc file to finish:${BR}"
  printf "##### \"source ${USER_HOME}/${RC_FILE}\" ${BR}"
  printf "${FONT_NONE}"
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
      echo "installation" >&2
      installation
      success
      ;;
    u)
      echo "update" >&2
      update
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
