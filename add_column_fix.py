import sys
import os
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255)"))
        db.session.commit()
        print("Successfully added avatar_url column to users table.")
    except Exception as e:
        print(f"Error adding column: {e}")
        db.session.rollback()
