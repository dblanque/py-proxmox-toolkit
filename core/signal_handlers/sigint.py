import sys
def graceful_exit(sig, frame):
	print('\nCtrl+C Received, cancelling script.')
	sys.exit(0)
