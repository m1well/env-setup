#!/bin/bash
###
#title                  : m1well-toolsuite.sh
#description            : This script provides a setup for the m1well-toolsuite.
#author                 : Michael Wellner (@m1well)
#date of creation       : 20181210
#date of last change    : 20260729
#version                : 3.0.0
#usage                  : m1well-toolsuite.sh [-i|-u]
#notes                  : prerequisites
#                       : debian / ubuntu (e.g. a docker container) -- run this to get git: "apt-get update && apt-get -y install git vim"
#                       : osx with homebrew -- run: "brew update && brew install git"
#                       : for vim and zsh styling - you need vim, zsh and oh-my-zsh installed
#                       : to run this script you have to do following steps (wherever you want):
#                       : execute "mkdir m1well-toolsuite && cd m1well-toolsuite && git clone https://github.com/m1well/env-setup.git && cd env-setup"
#                       : ---
###

set -eu

### constants ###
FONT_CYAN="\033[0;96m"
FONT_GREEN="\033[0;92m"
FONT_NONE="\033[0m"
HASHLINE="######################################################"
HEADER="################## m1well toolsuite ##################"
FONT_CASK="font-inconsolata-nerd-font"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLSUITE_HOME="$(dirname "${SCRIPT_DIR}")"

printStartLines() {
  printf '%b' "${FONT_CYAN}"
  printf '%s\n' "${HASHLINE}"
  printf '%s\n' "${HEADER}"
  printf '%s\n' "${HASHLINE}"
  printf '%b' "${FONT_NONE}"
}

printEndLines() {
  printf '%b' "${FONT_CYAN}"
  printf '%s\n' "${HASHLINE}"
  printf '%b' "${FONT_NONE}"
}

printSuccess() {
  if [ -f "${HOME}/.zshrc" ]; then
    local file="${HOME}/.zshrc"
  else
    local file="${HOME}/.bashrc"
  fi
  printf '%b' "${FONT_GREEN}"
  printf '##### succeeded\n'
  printf '##### if you added the iterm2 profile file you have to set it as default profile\n'
  printf '##### now you have to source your rc file to finish:\n'
  printf '##### "source %s"\n' "${file}"
  printf '%b' "${FONT_NONE}"
}

printUsage() {
  echo "Invalid option - you can only use -i for installation or -u for update" >&2
}

installTools() {
  cd "${TOOLSUITE_HOME}"
  if [ -d cheatsheet ]; then
    printf '## cheatsheet project apparently already exists\n'
  else
    git clone https://github.com/m1well/cheatsheet.git
  fi
  if [ -d versions ]; then
    printf '## versions project apparently already exists\n'
  else
    git clone https://github.com/m1well/versions.git
  fi
  if [ -d randomizer ]; then
    printf '## randomizer project apparently already exists\n'
  else
    git clone https://github.com/m1well/randomizer.git
  fi
}

copyCliMaster() {
  cp "${SCRIPT_DIR}/dotfiles/.m1well_cli_master" "${HOME}/.m1well_cli_master"
}

copyIndividualCliFiles() {
  cp "${SCRIPT_DIR}/templates/.cli_private" "${SCRIPT_DIR}/cli/.cli_private"
}

replaceString() {
  if [[ "${OSTYPE}" == darwin* ]]; then
    sed -i -temp -e "s|${2}|${3}|g" "${1}"
    rm "${1}-temp"
  else
    sed -e "s|${2}|${3}|g" "${1}" > "${1}-temp"
    mv "${1}-temp" "${1}"
  fi
}

stripSshBlock() {
  local tmp="${1}.tmp"
  awk '
    /^# >>> m1well-toolsuite >>>$/ { skip = 1 ; next }
    skip && /^# <<< m1well-toolsuite <<<$/ { skip = 0 ; next }
    !skip
  ' "${1}" > "${tmp}"
  mv "${tmp}" "${1}"
}

generateRcFile() {
  local rcFile="${HOME}/${RC_FILE}"
  if [ -e "${rcFile}" ] && grep -q "m1well-toolsuite" "${rcFile}"; then
    printf '## toolsuite block already present - skipping\n'
    return
  fi
  cp "${RC_TEMPLATE_FILE}" "${RC_TEMPLATE_FILE}.copy"
  replaceString "${RC_TEMPLATE_FILE}.copy" "&&toolsuitehome&&" "${TOOLSUITE_HOME}"
  replaceString "${RC_TEMPLATE_FILE}.copy" "&&useiterm2&&" "${USE_ITERM2}"
  if [ -e "${rcFile}" ]; then
    cat "${rcFile}" >> "${RC_TEMPLATE_FILE}.copy"
  fi
  mv "${RC_TEMPLATE_FILE}.copy" "${rcFile}"
}

generateGitTemplate() {
  rm -f "${HOME}/.gittemplate"
  cat "${SCRIPT_DIR}/dotfiles/.gittemplate" > "${HOME}/.gittemplate"
}

disableIterm2() {
  USE_FONT=false
  USE_ITERM2=false
}

installFontIfNeeded() {
  if [ "${USE_FONT}" != true ]; then
    return
  fi
  if [[ "${OSTYPE}" != darwin* ]]; then
    printf '## font install skipped - homebrew cask fonts are macOS only (looks like linux/docker here)\n'
    return
  fi
  if ! command -v brew >/dev/null; then
    printf '## font install skipped - homebrew not found\n'
    printf '## install the font manually with: brew install --cask %s\n' "${FONT_CASK}"
    return
  fi
  printf '## installing font via homebrew: %s\n' "${FONT_CASK}"
  brew install --cask "${FONT_CASK}" || printf '## font install failed - continuing anyway\n'
}

createSshConfig() {
  local sshDir="${HOME}/.ssh"
  local sshConfig="${sshDir}/config"
  local keyFile="${sshDir}/id_ed25519_github"
  mkdir -p "${sshDir}"
  chmod 700 "${sshDir}"

  if [ -f "${keyFile}" ]; then
    printf '## ssh key already exists, skipping keygen\n'
  else
    local keyComment
    keyComment="$(git config -f "${SCRIPT_DIR}/dotfiles/.gitconfig" --get user.email 2>/dev/null || true)"
    ssh-keygen -t ed25519 -f "${keyFile}" -C "${keyComment}"
  fi

  if [ -f "${sshConfig}" ]; then
    grep -q '^# >>> m1well-toolsuite >>>$' "${sshConfig}" && stripSshBlock "${sshConfig}"
    [ -n "$(tail -c1 "${sshConfig}")" ] && printf '\n' >> "${sshConfig}"
  fi
  {
    printf '# >>> m1well-toolsuite >>>\n'
    printf '# defaults\nHost *\n  AddressFamily inet\n  Protocol 2\n  Compression yes\n  ServerAliveInterval 60\n'
    printf '\n# github ssh\nHost github.com\n  HostName github.com\n  User git\n  IdentityFile %s\n  IdentitiesOnly yes\n' "${keyFile}"
    printf '# <<< m1well-toolsuite <<<\n'
  } >> "${sshConfig}"
  chmod 600 "${sshConfig}"

  printf 'copy following public key to your github account and then change your remotes from https url to ssh url:\n\n'
  cat "${keyFile}.pub"
  printf '\n\n'
}

askQuestion() {
  read -rn1 -p "${1} (y/n)? "
  echo ""
}

installation() {
  RC_FILE=".zshrc"
  RC_TEMPLATE_FILE="${SCRIPT_DIR}/templates/.rc_template"
  USE_FONT=true
  USE_ITERM2=true
  copyCliMaster
  copyIndividualCliFiles
  askQuestion "iterm2 installed and want to use m1well profile?"
  [[ ! $REPLY =~ ^[Yy]$ ]] && disableIterm2
  installFontIfNeeded
  askQuestion "generate ssh config and ssh key for github?"
  [[ $REPLY =~ ^[Yy]$ ]] && createSshConfig
  generateRcFile
  generateGitTemplate
  mkdir -p "${HOME}/.config/nvim"
  mkdir -p "${HOME}/.claude"
  installTools
}

update() {
  local failed=0
  for dir in "${TOOLSUITE_HOME}"/*/; do
    local name; name="$(basename "${dir}")"
    if [ ! -d "${dir}.git" ]; then
      printf '## skipping (not a git repo): %s\n' "${name}"
      continue
    fi
    printf '## updating %s\n' "${name}"
    if ! (cd "${dir}" && git pull --ff-only); then
      printf '## update failed (resolve manually): %s\n' "${name}"
      failed=$((failed + 1))
    fi
  done
  generateGitTemplate
  if [ "${failed}" -gt 0 ]; then
    printf '## %s repo(s) could not be updated - see above\n' "${failed}"
  fi
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
cd "${TOOLSUITE_HOME}"

printEndLines

### end of script ###

#####################
