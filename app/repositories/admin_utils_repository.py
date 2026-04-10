from app.models.knowledge_base import KnowledgeBase
from app.models.report import Report
from app.models.contact import Contact
from app.models.audit_log import AdminAuditLog
from app.models.blocked_user import BlockedUser
from app.repositories.base_repository import BaseRepository

class KnowledgeBaseRepository(BaseRepository):
    def __init__(self):
        super().__init__(KnowledgeBase)

    def search_by_title(self, query):
        return self.model.query.filter(self.model.title.ilike(f"%{query}%")).all()

    def search_content(self, query, limit=5):
        # Tách các từ khóa để tìm kiếm linh hoạt hơn
        keywords = query.split()
        filters = []
        for kw in keywords:
            if len(kw) > 1: # Chỉ tìm các từ có nghĩa (bỏ qua 'a', 'i', etc.)
                filters.append(
                    (self.model.title.ilike(f"%{kw}%")) | 
                    (self.model.content.ilike(f"%{kw}%"))
                )
        
        if not filters:
            return []

        # Sử dụng OR giữa các từ khóa để tăng khả năng tìm thấy, 
        # nhưng AI sẽ lọc lại ở bước sau nên không lo bị loãng.
        from sqlalchemy import or_
        return self.model.query.filter(or_(*filters)).limit(limit).all()

class ReportRepository(BaseRepository):
    def __init__(self):
        super().__init__(Report)

    def get_by_reporter(self, reporter_id):
        return self.model.query.filter_by(reporter_id=reporter_id).order_by(self.model.created_at.desc()).all()

class ContactRepository(BaseRepository):
    def __init__(self):
        super().__init__(Contact)

    def get_user_contacts(self, user_id):
        return self.model.query.filter_by(user_id=user_id).all()

    def remove_contact(self, user_id, colleague_id):
        from app.extensions import db
        contact = self.model.query.filter_by(user_id=user_id, colleague_id=colleague_id).first()
        if contact:
            db.session.delete(contact)
            db.session.commit()
            return True
        return False

class AuditLogRepository(BaseRepository):
    def __init__(self):
        super().__init__(AdminAuditLog)

class BlockedUserRepository(BaseRepository):
    def __init__(self):
        super().__init__(BlockedUser)

    def is_blocked(self, user_id, target_user_id):
        return self.model.query.filter_by(user_id=user_id, blocked_user_id=target_user_id).first() is not None
