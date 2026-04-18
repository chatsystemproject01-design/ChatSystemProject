# wsgi.py - Entry point cho Gunicorn trên Production
import os
from app import create_app

app = create_app()
