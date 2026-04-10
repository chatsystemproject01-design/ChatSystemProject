from app.extensions import db
from datetime import datetime

class ChatSummary(db.Model):
    __tablename__ = 'chat_summaries'
    
    summary_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.conversation_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.dialects.postgresql.UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatSummary conv={self.conversation_id}>"
