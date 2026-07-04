"""Offline FAQ chatbot — returns predefined answers about phishing & cybersecurity.
No external API calls needed. Runs entirely on the backend."""

import re

FAQ = [
    {
        "keywords": ["what is phishing", "define phishing", "phishing meaning", "explain phishing", "phishing kya"],
        "answer": (
            "**Phishing** is a type of cyber attack where criminals impersonate legitimate "
            "companies (banks, PayPal, Google, Amazon) to trick you into revealing sensitive "
            "information like passwords, credit card numbers, or personal data.\n\n"
            "Common phishing methods:\n"
            "- **Email phishing**: Fake emails that look like they're from real companies\n"
            "- **Spear phishing**: Targeted attacks aimed at specific individuals\n"
            "- **Smishing**: Phishing via SMS/text messages\n"
            "- **Vishing**: Phishing via phone calls\n\n"
            "**Red flags to watch for:**\n"
            "• Urgent language (\"Your account will be closed!\")\n"
            "• Suspicious sender email addresses\n"
            "• Generic greetings (\"Dear Customer\" instead of your name)\n"
            "• Requests for passwords or personal information\n"
            "• Misspellings and poor grammar\n"
            "• Suspicious links (hover before clicking!)"
        )
    },
    {
        "keywords": ["how to detect phishing", "identify phishing", "spot phishing", "recognize phishing", "phishing detection tips"],
        "answer": (
            "**How to detect phishing attacks:**\n\n"
            "**1. Check the URL carefully**\n"
            "• Look for misspellings (e.g., `paypa1.com` instead of `paypal.com`)\n"
            "• Check for suspicious TLDs (`.tk`, `.ml`, `.ga`, `.xyz`)\n"
            "• HTTPS doesn't mean safe — phishing sites also use HTTPS\n\n"
            "**2. Examine the email**\n"
            "• Check the sender's actual email address, not just the display name\n"
            "• Look for generic greetings instead of your name\n"
            "• Watch for urgent/threatening language\n\n"
            "**3. Hover before you click**\n"
            "• Hover over links to see the actual destination URL\n"
            "• If the link doesn't match the context, don't click\n\n"
            "**4. Use PhishGuard!**\n"
            "• Paste suspicious URLs into our scanner\n"
            "• Enable Real-Time Protection in the Chrome extension\n"
            "• Check the rule analysis and ML predictions"
        )
    },
    {
        "keywords": ["how does phishguard work", "how phishguard works", "phishguard detection", "phishguard mechanism", "phishguard kese"],
        "answer": (
            "**How PhishGuard Works — Dual-Layer Detection:**\n\n"
            "**Layer 1 — Rule-Based Analysis**\n"
            "• Checks 15+ security rules instantly:\n"
            "  - Suspicious TLDs (.tk, .ml, .xyz, .top)\n"
            "  - Brand impersonation (fake PayPal, Google, Amazon)\n"
            "  - IP address URLs (e.g., http://192.168.1.1)\n"
            "  - URL shorteners (bit.ly, tinyurl, etc.)\n"
            "  - Missing HTTPS / invalid SSL certificates\n"
            "  - Excessive subdomains and suspicious characters\n"
            "  - Domain age via WHOIS lookup\n\n"
            "**Layer 2 — Machine Learning Model**\n"
            "• Random Forest classifier with 150 decision trees\n"
            "• Trained on 500,000+ URLs\n"
            "• Extracts 31 structural features from each URL\n"
            "• ~91% accuracy on test data\n\n"
            "**Combined Verdict:**\n"
            "• **Safe (0-39)** → Green\n"
            "• **Risky (40-59)** → Orange/Yellow\n"
            "• **Phishing (60-100)** → Red"
        )
    },
    {
        "keywords": ["what is 2fa", "two factor authentication", "2 factor authentication", "mfa", "multi factor"],
        "answer": (
            "**Two-Factor Authentication (2FA)** adds an extra layer of security beyond just your password.\n\n"
            "Instead of only entering a password, 2FA requires **two different factors**:\n\n"
            "**1. Something you KNOW** (password or PIN)\n"
            "**2. Something you HAVE** (phone, hardware token) or **ARE** (fingerprint, face)\n\n"
            "**Common 2FA methods:**\n"
            "• **Authenticator apps** (Google Authenticator, Microsoft Authenticator, Authy)\n"
            "• **SMS codes** (text message — less secure but better than nothing)\n"
            "• **Hardware keys** (YubiKey, Google Titan)\n"
            "• **Biometrics** (fingerprint, face ID)\n\n"
            "**Why use 2FA?**\n"
            "Even if someone steals your password, they can't log in without the second factor.\n"
            "It blocks 99.9% of automated attacks according to Google."
        )
    },
    {
        "keywords": ["what is ransomware", "ransomware attack", "ransomware meaning"],
        "answer": (
            "**Ransomware** is a type of malware that encrypts your files and demands payment "
            "(usually in cryptocurrency) to restore access.\n\n"
            "**How ransomware spreads:**\n"
            "• Phishing emails with malicious attachments\n"
            "• Malicious links that download malware\n"
            "• Drive-by downloads from compromised websites\n"
            "• Remote Desktop Protocol (RDP) attacks\n\n"
            "**How to protect yourself:**\n"
            "• **Never** pay the ransom — it funds criminals and doesn't guarantee your files back\n"
            "• Regularly back up your important files (3-2-1 rule)\n"
            "• Keep your software and OS updated\n"
            "• Don't open suspicious email attachments\n"
            "• Use reputable antivirus/anti-malware software\n"
            "• Enable email filtering to block malicious attachments"
        )
    },
    {
        "keywords": ["how to stay safe online", "online safety tips", "internet security tips", "browse safely", "cyber safety"],
        "answer": (
            "**Top 10 Online Safety Tips:**\n\n"
            "**1. Use strong, unique passwords** — Use a password manager (Bitwarden, 1Password, LastPass)\n\n"
            "**2. Enable 2FA everywhere** — Especially on email, banking, and social media\n\n"
            "**3. Keep software updated** — Enable automatic updates for OS, browser, and apps\n\n"
            "**4. Think before you click** — Hover over links, verify sender email addresses\n\n"
            "**5. Use the PhishGuard extension** — Real-Time Protection blocks phishing sites\n\n"
            "**6. Don't reuse passwords** — Each account should have a unique password\n\n"
            "**7. Be careful on public WiFi** — Use a VPN on public networks\n\n"
            "**8. Check for HTTPS** — Look for the padlock icon in your browser\n\n"
            "**9. Don't overshare on social media** — Criminals use personal info for targeted attacks\n\n"
            "**10. Trust your instincts** — If something feels wrong, it probably is"
        )
    },
    {
        "keywords": ["what is url shortener", "url shortener safety", "bitly safe", "shortened url", "tinyurl"],
        "answer": (
            "**URL Shorteners** (like bit.ly, tinyurl, goo.gl, t.co) are services that convert "
            "long URLs into short, easy-to-share links.\n\n"
            "**The security risk:** Shortened URLs hide the actual destination. Attackers use them to:\n"
            "• Mask phishing links\n"
            "• Bypass email filters\n"
            "• Make malicious URLs look legitimate\n\n"
            "**PhishGuard protects you by:**\n"
            "1. Automatically detecting shortened URLs from 50+ shortener services\n"
            "2. Resolving them to the actual destination URL\n"
            "3. Checking the final URL for phishing indicators\n"
            "4. SSRF protection — blocks resolution to private/internal IPs\n\n"
            "Always use a URL expander or PhishGuard before clicking shortened links from unknown sources!"
        )
    },
    {
        "keywords": ["what is ssl", "ssl certificate", "tls", "https meaning", "what is https"],
        "answer": (
            "**SSL (Secure Sockets Layer)** and its successor **TLS (Transport Layer Security)** "
            "are protocols that encrypt data between your browser and a website.\n\n"
            "**What HTTPS does:**\n"
            "• Encrypts all data in transit (passwords, credit cards, messages)\n"
            "• Verifies the website's identity via SSL certificates\n"
            "• Prevents eavesdropping and man-in-the-middle attacks\n\n"
            "**How to check:**\n"
            "• Look for the padlock icon 🔒 in your browser's address bar\n"
            "• The URL should start with `https://` (not `http://`)\n"
            "• Click the padlock to see certificate details\n\n"
            "**⚠️ Important:** HTTPS alone does NOT mean a site is safe!\n"
            "Phishing sites also use HTTPS. Always check the domain name and use tools like PhishGuard."
        )
    },
    {
        "keywords": ["what is homograph attack", "homograph", "unicode attack", "lookalike domain", "idn homograph"],
        "answer": (
            "**Homograph Attacks** use lookalike characters from different alphabets to create "
            "fake domain names that look identical to real ones.\n\n"
            "**Example:**\n"
            "• `apple.com` (Latin 'a') vs `арple.com` (Cyrillic 'а') — they look the same!\n"
            "• The Cyrillic 'а' (U+0430) is visually identical to the Latin 'a' (U+0061)\n\n"
            "**How PhishGuard detects them:**\n"
            "• Scans for non-ASCII Unicode characters in URLs\n"
            "• Flags potential homograph attacks with high severity\n"
            "• Checks for mixed-script domains\n\n"
            "**How to protect yourself:**\n"
            "• Type important URLs manually instead of clicking links\n"
            "• Use browser features that display punycode (xn--...)\n"
            "• Let PhishGuard scan suspicious URLs before visiting"
        )
    },
    {
        "keywords": ["how to report phishing", "report phishing email", "report scam", "phishing report", "where to report"],
        "answer": (
            "**How to Report Phishing Attacks:**\n\n"
            "**In the US/UK:**\n"
            "• **FTC** (Federal Trade Commission): ReportFraud.ftc.gov\n"
            "• **APWG** (Anti-Phishing Working Group): reportphishing@apwg.org\n"
            "• **IC3** (FBI Internet Crime Complaint Center): ic3.gov\n\n"
            "**In Pakistan:**\n"
            "• **NR3C** (National Response Centre for Cyber Crime): nr3c.gov.pk\n"
            "• Call **1991** — FIA's cyber crime helpline\n"
            "• Email: nr3c@fia.gov.pk\n\n"
            "**For specific platforms:**\n"
            "• **Gmail**: Click \"Report spam\" or \"Report phishing\"\n"
            "• **Outlook**: Click \"Report message\" → \"Phishing\"\n"
            "• **Facebook/Instagram**: Use the built-in reporting tools\n"
            "• **PayPal**: Forward suspicious emails to spoof@paypal.com\n\n"
            "**Also:** Share the suspicious URL here on PhishGuard to help others!"
        )
    },
    {
        "keywords": ["what is malware", "malware meaning", "virus", "trojan", "spyware"],
        "answer": (
            "**Malware** (Malicious Software) is any software designed to harm or exploit computers.\n\n"
            "**Common types:**\n"
            "• **Virus** — Attaches to legitimate programs, spreads when executed\n"
            "• **Trojan** — Disguises as legitimate software, steals data\n"
            "• **Ransomware** — Encrypts files, demands payment\n"
            "• **Spyware** — Secretly monitors your activity\n"
            "• **Keylogger** — Records your keystrokes (captures passwords)\n\n"
            "**How malware spreads:**\n"
            "• Phishing emails with infected attachments\n"
            "• Fake software downloads\n"
            "• Malicious advertisements (malvertising)\n"
            "• USB drives\n"
            "• Exploit kits targeting unpatched software\n\n"
            "**Protection tips:**\n"
            "• Don't download from untrusted sources\n"
            "• Keep OS and software updated\n"
            "• Use antivirus software (Windows Defender is good)\n"
            "• Be careful with email attachments"
        )
    },
    {
        "keywords": ["phishguard features", "phishguard can do", "what can phishguard", "phishguard capabilities"],
        "answer": (
            "**PhishGuard Features — Complete Overview:**\n\n"
            "**🕸️ Web Interface:**\n"
            "• Single URL scanning with detailed results\n"
            "• Bulk scanning (up to 20 URLs at once)\n"
            "• Scan history and statistics dashboard\n"
            "• Pie chart visualization\n"
            "• AI Security Assistant (FAQs about phishing)\n\n"
            "**🔍 Detection Engine:**\n"
            "• Rule-based analysis (15+ security rules)\n"
            "• Machine Learning (Random Forest, 91% accuracy)\n"
            "• WHOIS domain age lookup\n"
            "• SSL certificate validation\n"
            "• URL shortener resolution with SSRF protection\n\n"
            "**🧩 Chrome Extension:**\n"
            "• Real-Time Protection — blocks phishing before page loads\n"
            "• Right-click context menu to scan URLs\n"
            "• Popup scanner for quick checks\n"
            "• Configurable API server URL\n"
            "• Auto API key provisioning\n\n"
            "**🔐 Security:**\n"
            "• API key authentication\n"
            "• Rate limiting\n"
            "• Security headers (CSP, X-Frame-Options, etc.)\n"
            "• SSRF protection in URL shortener resolver\n"
            "• HTTPS support"
        )
    },
]


def _normalize(text):
    """Normalize text for keyword matching."""
    return re.sub(r'[^\w\s]', '', text.lower()).strip()


def _find_best_match(message):
    """Find the best FAQ match for the given message."""
    normalized = _normalize(message)
    if not normalized:
        return None

    best_match = None
    best_score = 0

    for item in FAQ:
        for keyword in item["keywords"]:
            # Check if keyword appears in the message
            if keyword in normalized:
                # Longer keywords get higher priority (more specific match)
                score = len(keyword)
                if score > best_score:
                    best_score = score
                    best_match = item
                    break  # Found a match in this FAQ item

    return best_match


def get_faq_answer(message):
    """Get a FAQ answer for the given message. Returns a string."""
    match = _find_best_match(message)
    if match:
        return match["answer"]

    # No match found — return a helpful fallback with suggestions
    return (
        "I'm PhishGuard's offline security assistant. I can answer questions about:\n\n"
        "• **What is phishing?** — Definition, types, and examples\n"
        "• **How to detect phishing?** — Spotting fake emails and websites\n"
        "• **How PhishGuard works?** — Dual-layer detection system\n"
        "• **Online safety tips** — Passwords, 2FA, browsing safely\n"
        "• **What is 2FA?** — Two-factor authentication explained\n"
        "• **What is ransomware?** — Protection and recovery\n"
        "• **What is SSL/HTTPS?** — Encryption explained\n"
        "• **URL shorteners** — Risks and how we handle them\n"
        "• **Homograph attacks** — Fake lookalike domains\n"
        "• **How to report phishing?** — Authorities and procedures\n\n"
        "**Try asking one of these questions!** 💡"
    )
