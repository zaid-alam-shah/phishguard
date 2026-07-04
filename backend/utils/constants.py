"""Shared constants for phishing detection — single source of truth.

Used by both the ML feature extractor and the rule-based analyzer
so that lists stay in sync across both pipelines.
"""

SUSPICIOUS_TLDS = frozenset({
    '.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work',
    '.click', '.link', '.info', '.online', '.site', '.website',
    '.bid', '.cam', '.date', '.download', '.loan', '.men',
    '.review', '.stream', '.trade', '.win',
})

TARGETED_BRANDS = [
    'paypal', 'apple', 'amazon', 'microsoft', 'google', 'facebook',
    'netflix', 'bank', 'chase', 'wellsfargo', 'citibank', 'dropbox',
    'linkedin', 'instagram', 'twitter', 'outlook', 'office365',
    'icloud', 'americanexpress', 'ebay', 'adobe', 'hsbc',
]

SENSITIVE_KEYWORDS = [
    'login', 'signin', 'verify', 'secure', 'update', 'confirm',
    'account', 'banking', 'password', 'credential',
]

SHORTENERS = frozenset({
    'bit.ly', 'tinyurl', 'goo.gl', 't.co', 'ow.ly', 'is.gd',
    'buff.ly', 'adf.ly', 'bit.do',
})

PHISHING_PATH_PATTERNS = ['cgi-bin', 'webscr', 'cmd=']
