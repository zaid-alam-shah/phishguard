import re
from urllib.parse import urlparse


def validate_url(url):
    if not url or not url.strip():
        return False, 'URL is required'

    url = url.strip()

    if len(url) > 2048:
        return False, 'URL exceeds maximum length of 2048 characters'

    if not re.match(r'^https?://', url):
        url = 'http://' + url

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, 'Invalid URL: no domain found'
        if '.' not in parsed.netloc and parsed.netloc != 'localhost':
            return False, 'Invalid URL: no valid domain extension'
    except Exception:
        return False, 'Invalid URL format'

    return True, url


def sanitize_url(url):
    return url.strip()[:2048]
