from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'
    
    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.conversation_id'), nullable=False)
    sender_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    message_content = db.Column(db.Text, nullable=False) # Should be encrypted according to RULE.md
    message_type = db.Column(db.String(20), default='text') # text, file, image, etc.
    is_toxic = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    statuses = db.relationship('MessageStatus', backref='message', lazy=True)
    attachments = db.relationship('FileAttachment', backref='message', lazy=True)
    reports = db.relationship('Report', backref='reported_message', lazy=True)

    def __repr__(self):
        return f"<Message {self.message_id} sender={self.sender_id}>"
