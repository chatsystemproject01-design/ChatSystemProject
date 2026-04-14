from app import create_app
from app.utils.email import send_otp_email
import time
import sys

app = create_app()

with app.app_context():
    print("Testing send_otp_email (async)...", flush=True)
    send_otp_email("duydien3504@gmail.com", "123456")

    print("Waiting 10 seconds for background task to complete or timeout...", flush=True)
    time.sleep(10)
    print("Test script finished.", flush=True)
