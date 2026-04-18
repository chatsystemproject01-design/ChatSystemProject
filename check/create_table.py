from app import create_app
from app.extensions import db
from app.models.system_config import SystemConfig

app = create_app()
with app.app_context():
    SystemConfig.__table__.create(db.engine, checkfirst=True)
    print("Table system_configs created successfully.")
