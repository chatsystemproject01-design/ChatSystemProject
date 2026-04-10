from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    conversation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(255))
    is_group = db.Column(db.Boolean, default=False)

    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    participants = db.relationship('ConversationParticipant', backref='conversation', lazy=True)
    messages = db.relationship('Message', backref='conversation', lazy=True)
    summaries = db.relationship('ChatSummary', backref='conversation', lazy=True)

    def __repr__(self):
        return f"<Conversation {self.conversation_id} group={self.is_group}>"
