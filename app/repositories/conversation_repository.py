from app.models.conversation import Conversation
from app.repositories.base_repository import BaseRepository

class ConversationRepository(BaseRepository):
    def __init__(self):
        super().__init__(Conversation)

    def get_user_conversations(self, user_id):
        from app.models.participant import ConversationParticipant
        return self.model.query.join(ConversationParticipant)\
            .filter(ConversationParticipant.user_id == user_id, self.model.is_deleted == False)\
            .order_by(self.model.created_at.desc()).all()

