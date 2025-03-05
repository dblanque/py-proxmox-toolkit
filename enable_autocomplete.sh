#!/bin/bash
ARGCOMPLETE_FILE="/etc/bash_completion.d/python-argcomplete"
BASH_COMPLETION_FILE="/etc/bash_completion"
BASH_COMPLETION_DIR="/etc/bash_completion.d"

if [ $(id -u) -ne 0 ]; then
	echo "Please run as root."
	exit 1
fi

if [[ ! "$workpath" ]]; then
	workpath="`dirname "$(realpath "$0")"`"
	cd "$workpath"
fi

apt update -y
apt install python3-argcomplete bash-completion
if [ $? -ne 0 ]; then
	echo "Could not install required dependencies."
	exit 1
fi

activate-global-python-argcomplete
if [ $? -ne 0 ]; then
	echo "Could not activate global argcomplete, is python3-argcomplete installed?"
	exit 2
fi

echo "You may also add this to your .bashrc if it doesn't work...
# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi"

echo "If it doesn't work, please make sure your $BASH_COMPLETION_DIR directory is being sourced!"
echo "To disable remove $ARGCOMPLETE_FILE"
exit 0