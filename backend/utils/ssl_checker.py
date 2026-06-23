import ssl
import socket
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

ssl_cache = {}


def check_ssl(url, timeout=5):
    try:
        parsed = urlparse(url if url.startswith('http') else 'http://' + url)
        hostname = parsed.hostname
        if not hostname:
            return None, None, None, None

        if hostname in ssl_cache:
            return ssl_cache[hostname]

        if parsed.scheme == 'http':
            result = (False, None, None, 'Uses HTTP (no SSL)')
            ssl_cache[hostname] = result
            return result

        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((hostname, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    result = (False, None, None, 'No certificate returned')
                    ssl_cache[hostname] = result
                    return result

                not_after_str = cert.get('notAfter', '')
                if not not_after_str:
                    result = (True, None, None, 'No expiry date in cert')
                    ssl_cache[hostname] = result
                    return result

                not_after = datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z')
                if not_after.tzinfo is None:
                    not_after = not_after.replace(tzinfo=timezone.utc)

                now = datetime.now(timezone.utc)
                days_left = (not_after - now).days

                issuer = dict(x[0] for x in cert.get('issuer', []) if x).get('organizationName', 'Unknown')

                is_valid = days_left > 0

                result = (is_valid, days_left, issuer, None)
                ssl_cache[hostname] = result
                return result

    except ssl.CertificateError as e:
        logger.warning(f'SSL certificate error for {hostname}: {e}')
        return (False, None, None, f'Certificate error: {str(e)[:60]}')
    except socket.timeout:
        logger.warning(f'SSL check timeout for {hostname}')
        return (None, None, None, 'Connection timeout')
    except ConnectionRefusedError:
        logger.warning(f'SSL connection refused for {hostname}')
        return (None, None, None, 'Connection refused')
    except Exception as e:
        logger.warning(f'SSL check failed: {e}')
        return (None, None, None, f'Check failed: {str(e)[:60]}')


def get_ssl_risk_issues(url):
    is_valid, days_left, issuer, error = check_ssl(url)

    issues = []
    risk_score = 0

    if is_valid is None:
        issues.append({
            'severity': 'medium',
            'text': f'Could not verify SSL certificate'
        })
        risk_score += 10
        return issues, risk_score

    if is_valid is False:
        if error:
            issues.append({
                'severity': 'high',
                'text': f'SSL issue: {error}'
            })
        else:
            issues.append({
                'severity': 'high',
                'text': 'SSL certificate is invalid or expired'
            })
        risk_score += 35
    else:
        if days_left is not None:
            if days_left < 7:
                issues.append({
                    'severity': 'high',
                    'text': f'SSL certificate expires in {days_left} days — critical'
                })
                risk_score += 30
            elif days_left < 30:
                issues.append({
                    'severity': 'medium',
                    'text': f'SSL certificate expires in {days_left} days'
                })
                risk_score += 15
            elif days_left < 90:
                issues.append({
                    'severity': 'low',
                    'text': f'SSL certificate expires in {days_left} days'
                })
                risk_score += 3
            elif error == 'Uses HTTP (no SSL)':
                issues.append({
                    'severity': 'medium',
                    'text': 'Uses HTTP instead of HTTPS'
                })
                risk_score += 15

    return issues, min(risk_score, 100)
