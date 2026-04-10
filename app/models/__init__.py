from app.extensions import db
from datetime import datetime

class BaseModel(db.Model):
    __abstract__ = True
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Import all models here to make them available
from .role import Role
from .user import User
from .otp import AuthOTP
from .ip_tracking import IPSecurityTracking
from .conversation import Conversation
from .participant import ConversationParticipant
from .message import Message
from .message_status import MessageStatus
from .file_attachment import FileAttachment
from .chat_summary import ChatSummary
from .knowledge_base import KnowledgeBase
from .report import Report
from .contact import Contact
from .audit_log import AdminAuditLog
from .blocked_user import BlockedUser
