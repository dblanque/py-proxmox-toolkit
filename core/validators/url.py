from urllib.parse import urlparse
def url_validator(value) -> bool:
    try:
        result = urlparse(value)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False