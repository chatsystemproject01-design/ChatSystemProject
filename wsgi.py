# wsgi.py - Entry point cho Gunicorn trên Production
# KHÔNG monkey_patch ở đây - Gunicorn eventlet worker tự xử lý
from app import create_app
from app.extensions import socketio

app = create_app()
