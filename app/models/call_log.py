from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime
import uuid

class CallLog(db.Model):
    __tablename__ = 'call_logs'
    
    call_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caller_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    receiver_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    call_type = db.Column(db.String(20), nullable=False) # voice, video
    status = db.Column(db.String(20), default='initiated') # initiated, ongoing, completed, missed, rejected, cancelled
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True) # seconds
    
    # Relationships
    caller = db.relationship('User', foreign_keys=[caller_id], backref='calls_made')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='calls_received')

    def __repr__(self):
        return f"<CallLog {self.call_id} type={self.call_type} status={self.status}>"
