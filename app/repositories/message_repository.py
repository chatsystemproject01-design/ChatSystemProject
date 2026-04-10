from app.models.message import Message
from app.repositories.base_repository import BaseRepository

class MessageRepository(BaseRepository):
    def __init__(self):
        super().__init__(Message)

    def get_conversation_messages(self, conversation_id, offset=0, limit=50):
        return self.model.query.filter_by(conversation_id=conversation_id, is_deleted=False)\
            .order_by(self.model.created_at.desc())\
            .offset(offset).limit(limit).all()
