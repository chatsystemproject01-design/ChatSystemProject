import eventlet
eventlet.monkey_patch(all=True)

import os

import warnings

# Bỏ qua cảnh báo Deprecation của Eventlet để log gọn hơn
warnings.filterwarnings("ignore", category=DeprecationWarning)

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    # Render cung cấp biến PORT qua Environment Variable. Nếu không có (như ở local) thì dùng 5000.
    port = int(os.environ.get('PORT', 5000))
    
    # Chỉ in log 1 lần khi Werkzeug chạy main process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or (app.config.get('FLASK_ENV') != 'development'):
        print(f">>> [SERVER] Ứng dụng đang chạy trên: http://0.0.0.0:{port}", flush=True)
        print(f">>> [DOCS] Swagger UI: http://0.0.0.0:{port}/apidocs", flush=True)

    socketio.run(
        app, 
        host='0.0.0.0', # Rất quan trọng: Phải là 0.0.0.0 để Render truy cập được
        port=port, 
        debug=(app.config.get('FLASK_ENV') == 'development'),
        use_reloader=False
    )
