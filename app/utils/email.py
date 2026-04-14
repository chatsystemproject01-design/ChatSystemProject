from flask_mail import Message
from app.extensions import mail
from flask import current_app
from datetime import datetime
import sys

def send_async_email(app, msg):
    """
    Hàm thực hiện gửi email trong App Context
    """
    with app.app_context():
        try:
            print(f">>> [EMAIL] Đang kết nối tới SMTP Server (465/SSL) để gửi đến {msg.recipients}...", flush=True)
            mail.send(msg)
            print(f">>> [SUCCESS] Đã gửi OTP thành công tới {msg.recipients}", flush=True)
        except Exception as e:
            error_msg = f">>> [EMAIL ERROR] Thất bại khi gửi tới {msg.recipients}. Lỗi: {str(e)}"
            print(error_msg, file=sys.stderr, flush=True)

def send_otp_email(to_email, otp_code):
    """
    Gửi mã OTP xác thực qua email.
    Sử dụng eventlet.spawn để chạy ngầm (tương thích hoàn toàn với Gunicorn eventlet)
    """
    subject = "Mã xác thực tài khoản - Nội bộ"
    body = f"Chào bạn,\n\nMã OTP kích hoạt tài khoản của bạn là: {otp_code}\n\nMã này có hiệu lực trong 5 phút.\n\nTrân trọng."
    
    msg = Message(subject, recipients=[to_email], body=body)
    
    if current_app:
        app = current_app._get_current_object()
        
        # Sử dụng cơ chế chạy ngầm của chính Eventlet để tránh xung đột Threading trên Linux
        try:
            import eventlet
            eventlet.spawn(send_async_email, app, msg)
            print(f">>> [QUEUED] Đã đưa email gửi đến {to_email} vào hàng chờ ngầm (Eventlet).", flush=True)
        except ImportError:
            # Fallback nếu không có eventlet (ví dụ ở môi trường khác)
            import threading
            thread = threading.Thread(target=send_async_email, args=(app, msg))
            thread.start()
            print(f">>> [QUEUED] Đã đưa email vào hàng chờ ngầm (Threading).", flush=True)
    else:
        print(">>> [EMAIL ERROR] Không tìm thấy Application Context để gửi email.", file=sys.stderr, flush=True)
