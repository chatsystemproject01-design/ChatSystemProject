from flask_mail import Message
from app.extensions import mail
from flask import current_app
from datetime import datetime
import sys
import concurrent.futures

# Sử dụng ThreadPoolExecutor để quản lý các luồng gửi thư
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

def send_async_email(app, msg):
    with app.app_context():
        try:
            print(f">>> [EMAIL] Đang kết nối tới SMTP Server để gửi đến {msg.recipients}...", flush=True)
            # Log config để debug (không log mật khẩu)
            print(f">>> [DEBUG] SMTP Server: {app.config.get('MAIL_SERVER')}:{app.config.get('MAIL_PORT')}", flush=True)
            
            mail.send(msg)
            
            print(f">>> [SUCCESS] Đã gửi OTP thành công tới {msg.recipients}", flush=True)
            try:
                with open("email_success.log", "a") as f:
                    f.write(f"Email sent to {msg.recipients} at {datetime.now()}\n")
            except: pass
        except Exception as e:
            error_msg = f">>> [EMAIL ERROR] Thất bại khi gửi tới {msg.recipients}. Lỗi: {str(e)}"
            print(error_msg, file=sys.stderr, flush=True)
            try:
                with open("email_error.log", "a") as f:
                    f.write(f"{error_msg} at {datetime.now()}\n")
            except: pass

def send_otp_email(to_email, otp_code):
    """
    Gửi mã OTP xác thực qua email.
    Sử dụng executor để chạy ngầm, tránh làm chậm hoặc treo request.
    """
    subject = "Mã xác thực tài khoản - Nội bộ"
    body = f"Chào bạn,\n\nMã OTP kích hoạt tài khoản của bạn là: {otp_code}\n\nMã này có hiệu lực trong 5 phút.\n\nTrân trọng."
    
    msg = Message(subject, recipients=[to_email], body=body)
    
    # Lấy app object thực tế
    if current_app:
        app = current_app._get_current_object()
        # Đưa vào hàng chờ xử lý ngầm
        executor.submit(send_async_email, app, msg)
    else:
        print(">>> [EMAIL ERROR] Không tìm thấy Application Context để gửi email.", file=sys.stderr, flush=True)
