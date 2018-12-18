#!/bin/bash
###
#title                  : m1well-test.sh
#description            : This script provides test for the m1well-toolsuite setup.
#author                 : Michael Wellner (@m1well) twitter.m1well.de
#date of creation       : 20181218
#date of last change    : 20181218
#version                : 0.1.0
#usage                  : m1well-test.sh
#notes                  :
###

### constants ###
BR="\n"
FONT_CYAN="\033[0;96m"
FONT_GREEN="\033[0;92m"
FONT_NONE="\033[0m"
HASHLINE="######################################################"

printLines() {
  printf "${FONT_CYAN}"
  printf "${HASHLINE}${BR}"
  printf "${FONT_NONE}"
}

isStringEqual() {
  if [ "${1}" == "${2}" ] ; then return 0 ; fi
  return 1
}
isCommandAvailable() {
  if command -v "${1}" >/dev/null; then return 0 ; fi
  return 1
}
### start of script ###

printLines

echo "test"

printLines

### end of script ###

#####################
