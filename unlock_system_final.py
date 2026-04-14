import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.system_config import SystemConfig

def unlock():
    app = create_app()
    with app.app_context():
        try:
            print("Connecting to Database...")
            configs = SystemConfig.query.all()
            if not configs:
                new_config = SystemConfig(is_maintenance_mode=False)
                db.session.add(new_config)
                print("Created new config with maintenance OFF.")
            else:
                for c in configs:
                    c.is_maintenance_mode = False
                    print(f"Updated config ID {c.id}: maintenance OFF.")
            
            db.session.commit()
            print("SUCCESS: System is now UNLOCKED.")
        except Exception as e:
            print(f"ERROR: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    unlock()
