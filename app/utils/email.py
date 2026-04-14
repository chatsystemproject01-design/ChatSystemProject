import concurrent.futures
import sys
from flask import current_app
from flask_mail import Message
from app.extensions import mail

# Sử dụng ThreadPoolExecutor - cực kỳ ổn định với worker kiểu gthread
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

def send_async_email(app, msg):
    with app.app_context():
        try:
            print(f">>> [EMAIL] Đang kết nối tới SMTP Server (SSL/TLS) để gửi đến {msg.recipients}...", flush=True)
            mail.send(msg)
            print(f">>> [SUCCESS] Đã gửi OTP thành công tới {msg.recipients}", flush=True)
        except Exception as e:
            error_msg = f">>> [EMAIL ERROR] Thất bại khi gửi tới {msg.recipients}. Lỗi: {str(e)}"
            print(error_msg, file=sys.stderr, flush=True)

def send_otp_email(to_email, otp_code):
    """
    Gửi mã OTP xác thực qua email (Chạy ngầm bằng ThreadPoolExecutor).
    """
    subject = "Mã xác thực tài khoản - Nội bộ"
    body = f"Chào bạn,\n\nMã OTP kích hoạt tài khoản của bạn là: {otp_code}\n\nMã này có hiệu lực trong 5 phút.\n\nTrân trọng."
    
    msg = Message(subject, recipients=[to_email], body=body)
    
    if current_app:
        app = current_app._get_current_object()
        executor.submit(send_async_email, app, msg)
        print(f">>> [QUEUED] Đã đưa email gửi đến {to_email} vào hàng chờ (ThreadBox).", flush=True)
    else:
        print(">>> [EMAIL ERROR] Không tìm thấy Application Context để gửi email.", file=sys.stderr, flush=True)
