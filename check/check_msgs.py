from app import create_app
from app.extensions import db
from app.models.message import Message

app = create_app()
with app.app_context():
    counts = {}
    for cid in [2, 4, 5, 6]:
        count = Message.query.filter_by(conversation_id=cid).count()
        counts[cid] = count
    print("Message counts:", counts)
