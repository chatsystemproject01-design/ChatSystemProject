from app import create_app
from flask_mail import Message
from app.extensions import mail

app = create_app()
with app.app_context():
    print("Testing email configuration...")
    msg = Message("Test Email Antigravity",
                  recipients=["chatsystem01@gmail.com"], # Thay thế bằng mail thật của bạn để test
                  body="Đây là email test cấu hình SMTP.")
    try:
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
