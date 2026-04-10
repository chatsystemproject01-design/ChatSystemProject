from app.extensions import db
from datetime import datetime

class IPSecurityTracking(db.Model):
    __tablename__ = 'ip_security_tracking'
    
    track_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(45), nullable=False)
    failed_count = db.Column(db.Integer, default=0)
    last_failed_at = db.Column(db.DateTime)
    is_blocked = db.Column(db.Boolean, default=False)
    block_until = db.Column(db.DateTime)

    def __repr__(self):
        return f"<IPSecurityTracking ip={self.ip_address} blocked={self.is_blocked}>"
