#!/bin/bash
###
#title                  : m1well-test.sh
#description            : This script provides test for the m1well-toolsuite setup.
#author                 : Michael Wellner (@m1well) twitter.m1well.de
#date of creation       : 20181218
#date of last change    : 20181220
#version                : 0.2.0
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
printCommandAvailable() {
  printf "command available: ${1} ${BR}"
}
printCommandNotAvailable() {
  printf "command not available: ${1} ${BR}"
}
printTestSucceeded() {
  printf "test succeeded: ${1} ${BR}"
}
printTestFailed() {
  printf "test failed: ${1} ${BR}"
}
isStringEqual() {
  if [[ "${1}" == "${2}" ]]; then return 0; fi
  return 1
}
isStringNotEmpty() {
  if [[ "${1}" != "" ]]; then return 0; fi
  return 1
}
matchesUuid() {
   if [[ "${1}" =~ [a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12} ]]; then return 0 ; fi
   return 1
}
matchesRandomNumberWith5Digits() {
   if [[ "${1}" =~ [0-9]{5} ]]; then return 0 ; fi
   return 1
}
matchesActualCalendarWeek() {
   if isStringEqual "${1}" "calendar week: $(date +"%V")"; then return 0 ; fi
   return 1
}
isAliasAvailable() {
  if alias "${1}" >/dev/null; then return 0; fi
  return 1
}
isCommandAvailable() {
  if command -v "${1}" >/dev/null; then
    return 0
  else
    printf "aaa"
    isAliasAvailable "${1}"
  fi
  return 1
}
sourceCliMasterFile() {
  source ~/.m1well_cli_master
}
failATest() {
  echo ""
  echo "_this shoud fail_"
  if isCommandAvailable "wxyz" ; then
    printCommandAvailable "wxyz"
  else
    printCommandNotAvailable "wxyz"
  fi
}
testUuid() {
  echo ""
  echo "_test uuid_"
  if isCommandAvailable "uuidgen"; then
    if isCommandAvailable "uuid"; then
      printCommandAvailable "uuid"
      if matchesUuid "$(uuid)"; then
        printTestSucceeded "uuid (generated an uuid)"
      else
        printTestFailed "uuid"
      fi
    else
      printCommandNotAvailable "uuid"
    fi
  else
    printCommandNotAvailable "uuidgen"
  fi
}
testRand() {
  echo ""
  echo "_test rand_"
  if isCommandAvailable "rand"; then
    printCommandAvailable "rand"
    if matchesRandomNumberWith5Digits "$(rand 5)"; then
      printTestSucceeded "rand (generated a random number with 5 digits)"
    else
      printTestFailed "rand"
    fi
  else
    printCommandNotAvailable "rand"
  fi
}
testWeek() {
  echo ""
  echo "_test week_"
  if isCommandAvailable "week"; then
    printCommandAvailable "week"
    if matchesActualCalendarWeek "$(week)"; then
      printTestSucceeded "week (get actual calendar week)"
    else
      printTestFailed "week"
    fi
  else
    printCommandNotAvailable "week"
  fi
}
testTimer() {
  echo ""
  echo "_test timer_"
  if isCommandAvailable "terminal-notifier"; then
    if isCommandAvailable "timer"; then
      printCommandAvailable "timer"
    else
      printCommandNotAvailable "timer"
    fi
  else
    printCommandNotAvailable "terminal-notifier"
  fi
}
testGitConf() {
  echo ""
  echo "_test gitconf_"
  if isCommandAvailable "git"; then
    if isCommandAvailable "gitconf"; then
      printCommandAvailable "gitconf"
      if isStringNotEmpty "$(gitconf)"; then
        printTestSucceeded "gitconf (printed out the git config)"
      else
        printTestFailed "gitconf"
      fi
    else
      printCommandNotAvailable "gitconf"
    fi
  else
    printCommandNotAvailable "git"
  fi
}
testCheatsheet() {
  echo ""
  echo "_test cheatsheet_"
  if isCommandAvailable "cheat" ; then
    printCommandAvailable "cheat"
    if echo "$(cheat -l all)" >/dev/null; then
      printTestSucceeded "cheat (get some output from 'cheat -l all')"
    else
      printTestFailed "cheat"
    fi
  else
    printCommandNotAvailable "cheat"
  fi
}
testVersions() {
  echo ""
  echo "_test versions_"
  if isCommandAvailable "versions" ; then
    printCommandAvailable "versions"
    if echo "$(versions)" >/dev/null; then
      printTestSucceeded "versions (get some output from 'versions')"
    else
      printTestFailed "versions"
    fi
  else
    printCommandNotAvailable "versions"
  fi
}
testRandomizer() {
  echo ""
  echo "_test randomizer_"
  if isCommandAvailable "randomizer" ; then
    printCommandAvailable "randomizer"
  else
    printCommandNotAvailable "randomizer"
  fi
}
testList() {
  echo ""
  echo "_test list_"
  if isCommandAvailable "list" ; then
    printCommandAvailable "list"
  else
    printCommandNotAvailable "list"
  fi
}

### start of script ###

shopt -s expand_aliases

printLines

sourceCliMasterFile
failATest
testUuid
testRand
testWeek
testTimer
testGitConf
testCheatsheet
testVersions
testRandomizer
testList
echo ""

printLines

### end of script ###

#####################
