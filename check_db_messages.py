from app import create_app
from app.extensions import db
from app.models.message import Message
from app.utils.crypto import CryptoUtils

app = create_app()
with app.app_context():
    messages = Message.query.order_by(Message.created_at.desc()).limit(20).all()
    for m in messages:
        try:
            content = CryptoUtils.decrypt(m.message_content)
            if 'tk' in content or 'cu' in content or 'alo' in content:
                print(f"Message ID: {m.message_id}, Content: {content}, Sender: {m.sender_id}")
        except Exception as e:
            print("Decrypt failed for msg_id:", m.message_id)
