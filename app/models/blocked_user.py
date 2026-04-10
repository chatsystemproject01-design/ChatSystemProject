import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class BlockedUser(db.Model):
    __tablename__ = 'blocked_users'
    
    block_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    blocked_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BlockedUser {self.user_id} -> {self.blocked_user_id}>"
