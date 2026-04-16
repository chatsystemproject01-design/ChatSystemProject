import os
import sys
import warnings

# Luôn đặt monkey_patch lên hàng đầu nếu có eventlet (tốt cho Railway/Linux)
try:
    import eventlet
    eventlet.monkey_patch()
    print(">>> [SYSTEM] Eventlet monkey patch applied.")
except ImportError:
    pass

# Bỏ qua cảnh báo Deprecation để log gọn hơn
warnings.filterwarnings("ignore", category=DeprecationWarning)

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    # Railway/Render cung cấp biến PORT qua Environment Variable. 
    port = int(os.environ.get('PORT', 5000))
    
    # Kiểm tra xem có đang ở chế độ dev không
    is_dev = (app.config.get('FLASK_ENV') == 'development')
    
    # Chỉ in log server khi bắt đầu (tránh in 2 lần khi dùng reloader)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not is_dev:
        print(f">>> [SERVER] Ứng dụng đang chạy trên: http://0.0.0.0:{port}", flush=True)

    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port, 
        debug=is_dev,
        use_reloader=is_dev,  # Tự động reload trên Windows, tắt trên Railway để ổn định
        allow_unsafe_werkzeug=True
    )
