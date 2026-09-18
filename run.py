import os
import sys
from pathlib import Path

# Ensure root directory is in python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app import create_app
from database.init_db import init_database

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'

    # Auto-initialize and seed DB on first run if needed
    try:
        init_database(app)
    except Exception as e:
        print(f"[Run Warning] Database initialization check encountered: {e}")

    print("=" * 65)
    print(" PASSPORT AUTOMATION SYSTEM — FULL-STACK WEB APPLICATION")
    print(f" Server running at: http://127.0.0.1:{port}")
    print("=" * 65)
    print(" DEMO CREDENTIALS:")
    print("  • Administrator: admin@passport.gov   / Admin@123")
    print("  • Officer:       officer@passport.gov / Officer@123")
    print("  • Applicant 1:   rajesh.sharma@example.com / Applicant@123")
    print("  • Applicant 2:   priya.patel@example.com   / Applicant@123")
    print("  • Applicant 3:   arun.kumar@example.com    / Applicant@123")
    print("=" * 65)

    app.run(host='127.0.0.1', port=port, debug=debug)
