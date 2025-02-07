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

if	[ ! -d "$BASH_COMPLETION_DIR" ] ||
	[ ! -f "$ARGCOMPLETE_FILE" ] ||
	[[ $1 == "-f" ]]; then
	activate-global-python-argcomplete
fi

if [ ! -f "$BASH_COMPLETION_FILE" ] || [[ $1 == "-f" ]]; then
	echo "Adding $BASH_COMPLETION_FILE file."
	echo \
"for file in $BASH_COMPLETION_DIR/* ; do
	source \"\$file\"
done" > "$BASH_COMPLETION_FILE"
fi

if [ $? -ne 0 ]; then
	echo "Could not activate global argcomplete, is python3-argcomplete installed?"
	exit 2
fi

echo "If it doesn't work, please make sure your $BASH_COMPLETION_DIR directory is being sourced!"
echo "To disable remove $ARGCOMPLETE_FILE"
exit 0