from app.models.participant import ConversationParticipant
from app.models.message_status import MessageStatus
from app.models.file_attachment import FileAttachment
from app.models.chat_summary import ChatSummary
from app.repositories.base_repository import BaseRepository

class ParticipantRepository(BaseRepository):
    def __init__(self):
        super().__init__(ConversationParticipant)

    def get_by_conversation_and_user(self, conversation_id, user_id):
        return self.model.query.filter_by(conversation_id=conversation_id, user_id=user_id).first()

class MessageStatusRepository(BaseRepository):
    def __init__(self):
        super().__init__(MessageStatus)

from app.models.message import Message

class FileAttachmentRepository(BaseRepository):
    def __init__(self):
        super().__init__(FileAttachment)

    def get_by_conversation(self, conversation_id):
        return self.model.query.join(Message).filter(Message.conversation_id == conversation_id).all()

class ChatSummaryRepository(BaseRepository):
    def __init__(self):
        super().__init__(ChatSummary)
