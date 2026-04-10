import os
from flask import Flask
from app.extensions import db
from app.config.settings import configs
from app.models import * # Import all models

app = Flask(__name__)
app.config.from_object(configs)
app.config['SQLALCHEMY_DATABASE_URI'] = configs.DATABASE_URL
db.init_app(app)

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Tables dropped.")
