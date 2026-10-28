import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import os
from app import create_app
from app.extensions import db
from app.models.user import User


def init_db():
    config_name = os.environ.get("FLASK_ENV", "production")
    app = create_app(config_name)
    with app.app_context():
        print("Ensuring database tables exist...")
        db.create_all()

        # Check if users already exist
        user_count = User.query.count()
        if user_count == 0:
            print("No users found. Seeding initial database...")
            from scripts.seed_database import seed
            seed()
        else:
            print(f"Database already initialized with {user_count} users. Skipping seed.")


if __name__ == "__main__":
    init_db()
