from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class ConversationParticipant(db.Model):
    __tablename__ = 'conversation_participants'
    
    participant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.conversation_id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    role_in_group = db.Column(db.String(20), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Participant conv={self.conversation_id} user={self.user_id}>"
