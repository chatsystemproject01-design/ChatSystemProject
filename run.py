import os
import sys
import warnings
import logging

# 1. Tắt toàn bộ cảnh báo phiền phức
warnings.filterwarnings("ignore")

# 2. Monkey Patch Eventlet (chỉ hiệu quả trên Linux/Railway, Windows sẽ bỏ qua hoặc chạy nhẹ)
try:
    import eventlet
    # Chặn stderr để dấu dòng log "RLock not greened" khi khởi động
    prev_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    eventlet.monkey_patch()
    sys.stderr = prev_stderr
except Exception:
    pass

# 3. Cấu hình logging: Chỉ hiện Log Request, ẩn Banner khởi động
logging.getLogger('werkzeug').setLevel(logging.INFO)

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == '__main__':
    # Tự động nhận diện Port (Local thường là 5000, Railway do hệ thống cấp)
    port = int(os.environ.get('PORT', 5000))
    is_dev = (app.config.get('FLASK_ENV') == 'development')
    
    # In thông tin Swagger UI đẹp mắt ra Console
    print("\n" + "="*60)
    print(f"🚀 SERVER CHAT ĐÃ SẴN SÀNG")
    print(f"🔗 Localhost Swagger: http://127.0.0.1:{port}/apidocs/")
    print(f"🔗 Network Swagger:   http://0.0.0.0:{port}/apidocs/")
    print("="*60 + "\n", flush=True)

    # Chạy Server
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port, 
        debug=is_dev,
        use_reloader=is_dev,
        allow_unsafe_werkzeug=True # Cần thiết để không bị lỗi trên môi trường Production
    )
