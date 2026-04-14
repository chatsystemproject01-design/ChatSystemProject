import os
import warnings

# Bỏ qua cảnh báo Deprecation để log gọn hơn
warnings.filterwarnings("ignore", category=DeprecationWarning)

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    # Render cung cấp biến PORT qua Environment Variable. 
    port = int(os.environ.get('PORT', 5000))
    
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or (app.config.get('FLASK_ENV') != 'development'):
        print(f">>> [SERVER] Ứng dụng đang chạy trên: http://0.0.0.0:{port}", flush=True)

    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port, 
        debug=(app.config.get('FLASK_ENV') == 'development'),
        use_reloader=False
    )
