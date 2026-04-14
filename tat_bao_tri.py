import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.system_config import SystemConfig

def check_and_fix():
    app = create_app()
    with app.app_context():
        configs = SystemConfig.query.all()
        print(f"Number of config rows: {len(configs)}")
        for i, c in enumerate(configs):
            print(f"Row {i}: id={c.id}, is_maintenance={c.is_maintenance_mode}")
            if c.is_maintenance_mode:
                c.is_maintenance_mode = False
                print(f"  -> Setting Row {i} to False")
        
        db.session.commit()
        print("Done.")

if __name__ == '__main__':
    check_and_fix()
