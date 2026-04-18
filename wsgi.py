# wsgi.py - Entry point cho Gunicorn trên Production
import gevent.monkey
gevent.monkey.patch_all()

# Xử lý deadlock của psycopg2 trên gevent
from psycogreen.gevent import patch_psycopg
patch_psycopg()

from app import create_app
from app.extensions import socketio

app = create_app()
