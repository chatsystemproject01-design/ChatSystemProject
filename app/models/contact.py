from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from datetime import datetime

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    contact_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    colleague_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Contact user={self.user_id} colleague={self.colleague_id}>"
