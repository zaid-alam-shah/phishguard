import logging
import socket
import ipaddress
from urllib.parse import urlparse

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

# IP ranges that should never be reached via URL unshortening (SSRF prevention)
PRIVATE_IP_RANGES = [
    ipaddress.ip_network('127.0.0.0/8'),       # Loopback
    ipaddress.ip_network('10.0.0.0/8'),         # Private
    ipaddress.ip_network('172.16.0.0/12'),      # Private
    ipaddress.ip_network('192.168.0.0/16'),     # Private
    ipaddress.ip_network('169.254.0.0/16'),     # Link-local
    ipaddress.ip_network('::1/128'),            # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),           # IPv6 unique local
    ipaddress.ip_network('fe80::/10'),          # IPv6 link-local
    ipaddress.ip_network('0.0.0.0/8'),          # Current network
    ipaddress.ip_network('100.64.0.0/10'),      # Carrier-grade NAT
    ipaddress.ip_network('198.18.0.0/15'),      # Benchmarking
]

# Cloud metadata IPs that are especially dangerous to allow
BLOCKED_HOSTNAMES = [
    '169.254.169.254',  # AWS/GCP/Azure metadata
    'metadata.google.internal',
    'metadata.goog',
    '100.100.100.200',  # Alibaba Cloud
]

# DNS resolution timeout in seconds
DNS_TIMEOUT = 3


def _is_private_ip(hostname):
    """Check if a hostname resolves to a private/internal IP address.

    Resolves both IPv4 and IPv6 addresses and checks against known
    private/internal IP ranges. Fails closed (blocks) on resolution errors
    to prevent SSRF bypasses.
    """
    # Save and set a short timeout for DNS resolution
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(DNS_TIMEOUT)
    try:
        # If it's already an IP string, check it directly
        try:
            addr = ipaddress.ip_address(hostname)
            return any(addr in network for network in PRIVATE_IP_RANGES)
        except ValueError:
            pass

        # Resolve hostname to IPs — use AF_UNSPEC to catch both IPv4 and IPv6
        addrs = socket.getaddrinfo(hostname, 80, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for addr in addrs:
            ip_str = addr[4][0]
            try:
                ip = ipaddress.ip_address(ip_str)
                if any(ip in network for network in PRIVATE_IP_RANGES):
                    return True
            except ValueError:
                continue
        return False
    except (socket.gaierror, socket.timeout, OSError):
        # If we can't resolve, err on the side of caution — block it
        logger.warning(f'Could not resolve hostname {hostname} (timeout={DNS_TIMEOUT}s), blocking to prevent SSRF')
        return True
    finally:
        socket.setdefaulttimeout(old_timeout)


def is_shortened(url):
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
        parsed = urlparse(url if url.startswith('http') else 'http://' + url)
        hostname = parsed.hostname or ''

        # SSRF check: block private/internal IPs
        hostname_lower = hostname.lower()
        if hostname_lower in BLOCKED_HOSTNAMES:
            logger.warning(f'Blocked SSRF attempt to {hostname}')
            return url, False

        if _is_private_ip(hostname):
            logger.warning(f'Blocked request to private/internal IP: {hostname}')
            return url, False

        resp = requests.head(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        final_url = resp.url
        was_redirected = len(resp.history) > 0
        if was_redirected:
            # Also check the final resolved URL for SSRF
            try:
                final_parsed = urlparse(final_url)
                final_hostname = final_parsed.hostname or ''
                if _is_private_ip(final_hostname) or final_hostname.lower() in BLOCKED_HOSTNAMES:
                    logger.warning(f'Blocked redirected request to private IP: {final_hostname}')
                    return url, False
            except Exception:
                pass
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
