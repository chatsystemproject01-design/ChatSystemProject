import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date)
    position = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='active')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    otps = db.relationship('AuthOTP', backref='user', lazy=True)
    sent_messages = db.relationship('Message', backref='sender', lazy=True)
    participants = db.relationship('ConversationParticipant', backref='user', lazy=True)
    message_statuses = db.relationship('MessageStatus', backref='user', lazy=True)
    contacts = db.relationship('Contact', foreign_keys='Contact.user_id', backref='owner', lazy=True)
    as_colleague = db.relationship('Contact', foreign_keys='Contact.colleague_id', backref='colleague', lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"
