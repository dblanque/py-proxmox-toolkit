#!/bin/bash
if [[ ! $scriptname ]]; then
	scriptname="`echo $BASH_SOURCE|awk -F "/" '{print $NF}'`"
fi

workpath=$(pwd)
if [ ${#1} -ge 1 ] && [ -d $1 ]; then
	workpath=$1
else
	echo "Provided path is not a valid directory."
	exit 1
fi

if [ -z $req ]; then
	req="requirements.txt"
fi

if ! [[ $(dpkg -l python3) ]] || ! [[ $(dpkg -l python3-venv) ]];then
	echo "Please install the following packages: python3 python3-venv"
	exit 1
fi

echo "[SCRIPT] | Creating virtualenv"
# virtualenv -p python3 "$workpath"
if [ -e "$workpath/bin/activate" ]; then
	python3 -m venv "$workpath" --upgrade
else
	python3 -m venv "$workpath"
fi

echo "[SCRIPT] | Activating virtualenv"
source "$workpath/bin/activate"

if [[ $? -ne 0 ]]; then
	echo "Couldn't activate Virtual Environment."
	exit $?
fi

echo "[SCRIPT] | Installing newest version of pip"
pip install --upgrade pip

if [ -f "$workpath/$req" ]; then
	echo "[SCRIPT] | Installing requirements.txt dependencies"
	pip3 install -r "$workpath/$req"
fi
