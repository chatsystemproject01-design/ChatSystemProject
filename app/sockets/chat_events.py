from app.extensions import socketio
from flask_socketio import emit

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Add more events like 'typing', 'message', etc.
