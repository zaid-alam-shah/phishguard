import logging
import requests

logger = logging.getLogger(__name__)

SHORTENER_DOMAINS = [
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 'is.gd',
    'buff.ly', 'adf.ly', 'bit.do', 'rb.gy', 'shorturl.at', 'cutt.ly',
    'shorte.st', 'clicky.me', 'v.gd', 'tiny.cc', 'bl.ink', 'bc.vc',
    'soo.gd', 's2r.co', 'u.to', 'clck.ru', 'short.cm', 'short.link',
    'shorturl.com', 'short.gy', 'korta.link', '1kb.link', 'tr.ee',
    'x.co', 'snipr.com', 'snipurl.com', 'shorl.com', 'filoops.info'
]


def is_shortened(url):
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url if url.startswith('http') else 'http://' + url)
        hostname = parsed.hostname or ''
        return any(s in hostname for s in SHORTENER_DOMAINS)
    except Exception:
        return False


def unshorten_url(url, timeout=5):
    if not is_shortened(url):
        return url, False

    try:
        resp = requests.head(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        final_url = resp.url
        was_redirected = resp.history and len(resp.history) > 0
        if was_redirected:
            logger.info(f'Unshortened: {url} -> {final_url}')
        return final_url, was_redirected
    except requests.exceptions.Timeout:
        logger.warning(f'Timeout unshortening {url}')
        return url, False
    except requests.exceptions.ConnectionError:
        logger.warning(f'Connection error unshortening {url}')
        return url, False
    except Exception as e:
        logger.warning(f'Error unshortening {url}: {e}')
        return url, False
