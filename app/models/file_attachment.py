from app.extensions import db
from datetime import datetime

class FileAttachment(db.Model):
    __tablename__ = 'files_attachments'
    
    file_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.message_id'), nullable=True)
    file_url = db.Column(db.String(512), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    magic_bytes_status = db.Column(db.String(50))
    is_secure = db.Column(db.Boolean, default=True)
    duration = db.Column(db.Integer, nullable=True) # Duration in seconds for voice/audio
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FileAttachment {self.file_name}>"
