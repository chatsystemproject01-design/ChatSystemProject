from app import create_app
from app.extensions import db
from app.models.call_log import CallLog

app = create_app()
with app.app_context():
    try:
        CallLog.__table__.create(db.engine)
        print("Success: created call_logs table")
    except Exception as e:
        print(f"Error (maybe already exists): {e}")
