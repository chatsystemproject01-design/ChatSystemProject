import eventlet
eventlet.monkey_patch()

import os

import warnings

# Bỏ qua cảnh báo Deprecation của Eventlet để log gọn hơn
warnings.filterwarnings("ignore", category=DeprecationWarning)

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    # Chỉ in log 1 lần khi Werkzeug chạy main process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or (app.config.get('FLASK_ENV') != 'development'):
        print("Server is running at: http://localhost:5000")
        print("Swagger UI: http://localhost:5000/apidocs")

    socketio.run(app, host='0.0.0.0', port=5000, debug=(app.config.get('FLASK_ENV') == 'development'))
