import re
def domain_validator(value) -> bool:
    """
    Single-Label allowing Domain Validator
    """
    pattern = r"^(((?:[*a-zA-Z0-9-.]){2,61}(?:\.[a-zA-Z]{2,})+|(?:[a-zA-Z0-9-]){2,64}))?$"
    try:
        if re.match(pattern, str(value)):
            return True
    except Exception as e:
        print(value)
        print(type(value))
        raise e
    return False

def reverse_domain_validator(value) -> bool:
    pattern = r"^((\d{1,3}\.){1,4}).*$"
    try:
        if re.match(pattern, str(value)):
            return True
    except Exception as e:
        print(value)
        print(type(value))
        raise e
    return False
