@echo off
REM ═══════════════════════════════════════════════════════════════
REM  PhishGuard — Generate Self-Signed SSL Certificates
REM  For development/testing only. For production, use Let's Encrypt.
REM ═══════════════════════════════════════════════════════════════

set CERT_DIR=%~dp0..\certs

if not exist "%CERT_DIR%" mkdir "%CERT_DIR%"

echo.
echo ═══════════════════════════════════════════════════════════════
echo  Generating self-signed SSL certificate for PhishGuard
echo  Certificates will be saved to: %CERT_DIR%
echo ═══════════════════════════════════════════════════════════════
echo.

REM Check if openssl is available
where openssl >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] OpenSSL is not installed or not in PATH.
    echo.
    echo To install OpenSSL on Windows:
    echo   Option 1: Download from https://slproweb.com/products/Win32OpenSSL.html
    echo   Option 2: Use Chocolatey: choco install openssl
    echo   Option 3: Use WSL: wsl openssl ...
    echo.
    echo Alternatively, use Python to generate certs:
    echo   python -c "import ssl; print(ssl.OPENSSL_VERSION)"
    echo.
    pause
    exit /b 1
)

REM Generate a private key and self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout "%CERT_DIR%\key.pem" -out "%CERT_DIR%\cert.pem" ^
    -days 365 -nodes -subj "/C=PK/ST=Sindh/L=Karachi/O=PhishGuard/CN=localhost" ^
    -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1"

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Certificate generation failed.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Certificates generated!
echo   Certificate: %CERT_DIR%\cert.pem
echo   Private Key: %CERT_DIR%\key.pem
echo.
echo To use with PhishGuard, add to your .env:
echo   SSL_CERT_PATH=%CERT_DIR%\cert.pem
echo   SSL_KEY_PATH=%CERT_DIR%\key.pem
echo.
echo For production, use Let's Encrypt (https://letsencrypt.org) instead.
echo.
pause
