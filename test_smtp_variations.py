import smtplib
from email.message import EmailMessage

HOST = "smtp.gmail.com"
PORT = 587
USER = "chatsystem@gmail.com"
# Thử cả 2 biến thể: có dấu cách và không có dấu cách
PASSWORDS = ["fngccdufixgyelrh", "fngc cduf ixgy elrh"]

for password in PASSWORDS:
    print(f"Testing with password: '{password}'...")
    try:
        server = smtplib.SMTP(HOST, PORT)
        server.starttls()
        server.login(USER, password)
        print(f"SUCCESS with password: '{password}'")
        server.quit()
        break
    except Exception as e:
        print(f"FAILED with password: '{password}'. Error: {e}")

print("\nTesting Port 465 (SSL)...")
for password in PASSWORDS:
    print(f"Testing SSL with password: '{password}'...")
    try:
        server = smtplib.SMTP_SSL(HOST, 465)
        server.login(USER, password)
        print(f"SUCCESS SSL with password: '{password}'")
        server.quit()
        break
    except Exception as e:
        print(f"FAILED SSL with password: '{password}'. Error: {e}")
