DEFAULT_CHOICES = {
	"yes":["yes","y"],
	"no":["no","n"]
}
def yes_no_input(
		msg: str,
		input_default=None,
		input_choices=DEFAULT_CHOICES
	):
	choices_str = '|'.join(input_choices)
	choices_str = f"({choices_str})"
	if input_default:
		default_str = f" [{input_choices['yes'][0].upper()}]"
	else: default_str = ""
	while True:
		r = input(f"{msg} {choices_str}{default_str}:")
		if r.lower() in input_choices["yes"]:
			return True
		elif r.lower() in input_choices["no"]:
			return False
		elif input_default == True or input_default in input_choices["yes"]:
			return True
		elif input_default == False or input_default in input_choices["no"]:
			return True
		else:
			print(f"Please enter a valid choice ({choices_str}).")