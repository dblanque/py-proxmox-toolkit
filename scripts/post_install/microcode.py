#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import signal
from core.signal_handlers.sigint import graceful_exit
signal.signal(signal.SIGINT, graceful_exit)