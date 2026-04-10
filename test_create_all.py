from app import create_app
from app.extensions import db
from app.models import *

app = create_app()
with app.app_context():
    print("Creating all tables via db.create_all()...")
    db.create_all()
    print("Tables created successfully.")
