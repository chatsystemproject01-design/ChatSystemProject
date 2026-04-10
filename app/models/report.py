from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class Report(db.Model):
    __tablename__ = 'reports'
    
    report_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reporter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    reported_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))
    reported_message_id = db.Column(db.Integer, db.ForeignKey('messages.message_id'))
    reason_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # pending, processed, dismissed
    processed_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'))
    admin_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reports_filed', lazy=True)
    reported_user = db.relationship('User', foreign_keys=[reported_user_id], backref='reports_received', lazy=True)
    processor = db.relationship('User', foreign_keys=[processed_by], backref='reports_handled', lazy=True)

    def __repr__(self):
        return f"<Report {self.report_id} by={self.reporter_id}>"
