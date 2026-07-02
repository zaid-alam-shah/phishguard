# ═══════════════════════════════════════════════════════════════
#  PhishGuard — Procfile for Render Web Service
#
#  Render uses this file to determine the process type and
#  command to run. The web process starts Gunicorn serving
#  the Flask application.
#
#  Build command (set in Render dashboard):
#    pip install -r requirements.txt
#
#  Environment variables (set in Render dashboard):
#    PYTHON_VERSION=3.11.0
#    FLASK_HOST=0.0.0.0
#    FLASK_PORT=10000  (Render assigns this dynamically)
#    SECRET_KEY=<generate a random one>
#    ADMIN_API_KEY=<generate a random one>
#    DATABASE_URL=<your PostgreSQL URL>  (for persistent storage)
# ═══════════════════════════════════════════════════════════════

web: gunicorn backend.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
