from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class MessageStatus(db.Model):
    __tablename__ = 'message_status'
    
    status_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.message_id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(20), default='sent') # sent, delivered, seen
    seen_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MessageStatus msg={self.message_id} user={self.user_id} status={self.status}>"
