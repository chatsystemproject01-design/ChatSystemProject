from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class AuthOTP(db.Model):
    __tablename__ = 'auth_otps'
    
    otp_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    otp_code = db.Column(db.String(10), nullable=False)
    expiration_time = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuthOTP user_id={self.user_id} code={self.otp_code}>"
