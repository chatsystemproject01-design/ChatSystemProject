from app.extensions import db
from datetime import datetime

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'
    
    doc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<KnowledgeBase {self.title}>"
