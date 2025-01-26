import logging
import sys
import os
from core.format.colors import bcolors

DEFAULT_LOG_FILE_LN_LIMIT=1000
LOG_FMT_THREAD = "%(asctime)s %(threadName)18s %(levelname)12s | %(message)s"
LOG_FMT = "%(asctime)s %(levelname)12s | %(message)s"
class ColoredFormatter(logging.Formatter):

	blue = bcolors.BLUE.value
	yellow = bcolors.YELLOW.value
	red = bcolors.L_RED.value
	bold_red = bcolors.RED.value
	reset = bcolors.NC.value

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.FORMATS = {
			logging.DEBUG: self.blue + self._fmt + self.reset,
			logging.INFO: self._fmt + self.reset,
			logging.WARNING: self.yellow + self._fmt + self.reset,
			logging.ERROR: self.red + self._fmt + self.reset,
			logging.CRITICAL: self.bold_red + self._fmt + self.reset
		}

	def format(self, record):
		log_fmt = self.FORMATS.get(record.levelno)
		formatter = logging.Formatter(log_fmt)
		return formatter.format(record)

def set_logger(
		logger: logging.Logger,
		log_console=True,
		log_file=None,
		level="INFO",
		error_log_file=None,
		threaded_logging=False,
		format=None
	):
	if not format:
		if threaded_logging: format = LOG_FMT_THREAD
		else: format = LOG_FMT
	log_level = getattr(logging, level)
	logger.setLevel(log_level)
	if log_file or error_log_file:
		log_formatter_file = logging.Formatter(format)
	if log_console:
		log_formatter_stream = ColoredFormatter(format)

	old_factory = logging.getLogRecordFactory()
	def record_factory(*args, **kwargs):
		record = old_factory(*args, **kwargs)
		record.threadName = '[{}]'.format(record.threadName)
		record.levelname = '[{}]'.format(record.levelname)
		return record
	logging.setLogRecordFactory(record_factory)

	# File Logger Handler
	log_handler_file = None
	if log_file:
		log_handler_file = logging.FileHandler(log_file)
		log_handler_file.setFormatter(log_formatter_file)
		log_handler_file.setLevel(log_level)

	log_handler_file_err = None
	if error_log_file:
		# Errors only Logger
		log_handler_file_err = logging.FileHandler(log_file)
		log_handler_file_err.setFormatter(log_formatter_file)
		log_handler_file_err.setLevel(logging.ERROR)
		logger.addHandler(log_handler_file_err)

	# Console Logger Handler
	log_handler_console = None
	if log_console:
		log_handler_console = logging.StreamHandler(sys.stdout)
		log_handler_console.setFormatter(log_formatter_stream)
		log_handler_console.setLevel(log_level)

	# Add handlers to logger
	if log_handler_file: logger.addHandler(log_handler_file)
	if log_handler_console:	logger.addHandler(log_handler_console)
	if log_handler_file_err: logger.addHandler(log_handler_file_err)
	return logger

def trim_log(log_file, log_line_limit=DEFAULT_LOG_FILE_LN_LIMIT):
	if os.path.isfile(log_file):
		with open(log_file, "r") as lf:
			lines = lf.readlines()
			if len(lines) < log_line_limit: return
			new_log_file = open(f"{log_file}.prev", "w")
			for ln in lines[-log_line_limit:]:
				new_log_file.write(ln)
		log_file = open(log_file, "w")
		log_file.close()
