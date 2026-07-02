#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  PhishGuard — Generate Self-Signed SSL Certificates
#  For development/testing only. For production, use Let's Encrypt.
# ═══════════════════════════════════════════════════════════════

set -e

CERT_DIR="$(cd "$(dirname "$0")/.." && pwd)/certs"

mkdir -p "$CERT_DIR"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo " Generating self-signed SSL certificate for PhishGuard"
echo " Certificates will be saved to: $CERT_DIR"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if openssl is available
if ! command -v openssl &> /dev/null; then
    echo "[ERROR] OpenSSL is not installed."
    echo "  Install: apt install openssl  or  brew install openssl"
    exit 1
fi

# Generate a private key and self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" \
    -days 365 -nodes \
    -subj "/C=PK/ST=Sindh/L=Karachi/O=PhishGuard/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1"

echo ""
echo "[SUCCESS] Certificates generated!"
echo "  Certificate: $CERT_DIR/cert.pem"
echo "  Private Key: $CERT_DIR/key.pem"
echo ""
echo "To use with PhishGuard, add to your .env:"
echo "  SSL_CERT_PATH=$CERT_DIR/cert.pem"
echo "  SSL_KEY_PATH=$CERT_DIR/key.pem"
echo ""
echo "For production, use Let's Encrypt (https://letsencrypt.org) instead."
echo ""
