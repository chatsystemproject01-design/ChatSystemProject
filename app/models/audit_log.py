from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class AdminAuditLog(db.Model):
    __tablename__ = 'admin_audit_logs'
    
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.String(50)) # ID of the entity affected
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('User', backref='audit_logs', lazy=True)

    def __repr__(self):
        return f"<AdminAuditLog admin={self.admin_id} action={self.action_type}>"
