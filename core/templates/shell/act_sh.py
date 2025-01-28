SCRIPT_NAME = "act.sh"

SCRIPT_TEMPLATE = """
#!/bin/sh

cd {toolkit_path}
python3 main.py scripts/general/update.py
"""
