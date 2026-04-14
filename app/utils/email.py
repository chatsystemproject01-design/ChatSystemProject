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

def send_otp_email(to_email, otp_code):
    """
    Gửi mã OTP xác thực qua email
    """
    subject = "Mã xác thực tài khoản - Nội bộ"
    body = f"Chào bạn,\n\nMã OTP kích hoạt tài khoản của bạn là: {otp_code}\n\nMã này có hiệu lực trong 5 phút.\n\nTrân trọng."
    
    msg = Message(subject, recipients=[to_email], body=body)
    
    try:
        mail.send(msg)
        print(f">>> Đã gửi OTP thành công tới {to_email}")
    except Exception as e:
        print(f">>> LỖI GỬI MAIL: {str(e)}")
        # Trong môi trường production, chúng ta nên log lại lỗi thay vì app crash
        raise e
