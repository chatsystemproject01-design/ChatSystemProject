from app import create_app
from app.utils.email import send_async_email
from flask_mail import Message
import sys

app = create_app()

with app.app_context():
    msg = Message("Test Email", recipients=["duydien3504@gmail.com"], body="Test from server")
    print("Sending test email...", flush=True)
    try:
        import app.extensions as ext
        ext.mail.send(msg)
        print("Success!", flush=True)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr, flush=True)
