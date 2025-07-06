from datetime import datetime, timezone, timedelta
import argparse

parser = argparse.ArgumentParser(
	prog="Date Threshold Calculator",
	description="Returns Boolean on timedelta based threshold.",
)
parser.add_argument(
	"-s", "--date-start", required=True, help="Must be in format %Y-%m-%dT%H:%M:%S%z"
)
parser.add_argument("-td", "--threshold-days", required=False, default=0, type=int)
parser.add_argument("-th", "--threshold-hours", required=False, default=0, type=int)
parser.add_argument("-tm", "--threshold-minutes", required=False, default=0, type=int)
parser.add_argument("-ts", "--threshold-seconds", required=False, default=0, type=int)
parser.add_argument(
	"-go",
	"--greater-only",
	required=False,
	default=False,
	action="store_true",
	help="Only return true if greater (default is greater or equal).",
)
parser.add_argument(
	"-us", "--microsecond-precision", required=False, default=False, action="store_true"
)
parser.add_argument(
	"-t",
	"--date-target",
	default=datetime.now().astimezone(timezone.utc),
	required=False,
	help="Must be in format %Y-%m-%dT%H:%M:%S%z",
)
args = parser.parse_args()
DATE_FMT = "%Y-%m-%dT%H:%M:%S%z"


def check_date_threshold():
	threshold = timedelta(
		days=args.threshold_days,
		hours=args.threshold_hours,
		minutes=args.threshold_minutes,
		seconds=args.threshold_seconds,
	)
	try:
		date_start = datetime.strptime(args.date_start, DATE_FMT).astimezone(
			timezone.utc
		)
	except:
		raise ValueError(f"date_start | Incorrect Date Format, must be {DATE_FMT}")
	if not isinstance(args.date_target, datetime):
		try:
			date_target = datetime.strptime(args.date_target, DATE_FMT).astimezone(
				timezone.utc
			)
		except:
			raise ValueError(f"date_target | Incorrect Date Format, must be {DATE_FMT}")
	else:
		date_target = args.date_target
	if not args.microsecond_precision:
		date_start = date_start.replace(microsecond=0)
		date_target = date_target.replace(microsecond=0)
	if args.greater_only:
		return date_target - date_start > threshold
	return date_target - date_start >= threshold


def main(**kwargs):
	try:
		print(check_date_threshold())
	except:
		raise


if __name__ == "__main__":
	main()
