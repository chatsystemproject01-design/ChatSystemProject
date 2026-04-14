from flask_mail import Message
from app.extensions import mail
from flask import current_app
import threading
from datetime import datetime

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            with open("email_success.log", "a") as f:
                f.write(f"Email sent to {msg.recipients} at {datetime.now()}\n")
        except Exception as e:
            # Rule 5: Log error
            error_msg = f"[Email Error] Failed to send email: {str(e)}"
            print(error_msg)
            with open("email_error.log", "a") as f:
                f.write(f"{error_msg} at {datetime.now()}\n")

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print(f">>> [SUCCESS] Đã gửi OTP thành công tới {msg.recipients}")
        except Exception as e:
            print(f">>> [EMAIL ERROR] {str(e)}")

def send_otp_email(to_email, otp_code):
    """
    Gửi mã OTP xác thực qua email (Chạy ngầm để không gây lỗi 502)
    """
    subject = "Mã xác thực tài khoản - Nội bộ"
    body = f"Chào bạn,\n\nMã OTP kích hoạt tài khoản của bạn là: {otp_code}\n\nMã này có hiệu lực trong 5 phút.\n\nTrân trọng."
    
    msg = Message(subject, recipients=[to_email], body=body)
    
    # Lấy app object thực tế
    app = current_app._get_current_object()
    
    # Chạy trong thread riêng để tránh làm timeout request
    import threading
    thread = threading.Thread(target=send_async_email, args=(app, msg))
    thread.start()
