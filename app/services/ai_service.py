from app.repositories import MessageRepository, ParticipantRepository, ChatSummaryRepository
from app.utils.ai_wrapper import AIWrapper
from app.utils.crypto import CryptoUtils
from app.utils.exceptions import ForbiddenError, ResourceNotFoundError, ValidationError
from app.extensions import db

class AIService:
    def __init__(self):
        self.message_repo = MessageRepository()
        self.participant_repo = ParticipantRepository()
        self.summary_repo = ChatSummaryRepository()

    def summarize_conversation(self, user_id, conversation_id, limit=100):
        # 1. Kiểm tra tư cách thành viên
        participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
        if not participant:
            raise ForbiddenError("Bạn không phải là thành viên của cuộc hội thoại này.")

        # 2. Lấy danh sách tin nhắn gần nhất kèm tên người gửi
        from app.models.message import Message
        from app.models.user import User
        
        # Query join để lấy tên người gửi thay vì ID
        messages_query = db.session.query(Message, User.full_name)\
            .join(User, Message.sender_id == User.user_id)\
            .filter(Message.conversation_id == conversation_id, Message.is_deleted == False)\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .all()

        if len(messages_query) < 3:
            raise ValidationError("Không đủ tin nhắn để tóm tắt (cần ít nhất 3 tin nhắn).")

        # 3. Gom và giải mã nội dung
        text_lines = []
        # messages_query trả về list các tuple (Message, full_name)
        for msg, full_name in reversed(messages_query):
            content = CryptoUtils.decrypt(msg.message_content)
            text_lines.append(f"{full_name}: {content}")
        
        full_text = "\n".join(text_lines)

        # 4. Gửi sang AI (Prompt đã được tối ưu trong AIWrapper)
        summary_text = AIWrapper.summarize(full_text)

        # 5. Lưu vào database
        summary_record = self.summary_repo.create(
            conversation_id=conversation_id,
            content=summary_text,
            created_by=user_id
        )

        return {
            "summary": summary_record.content,
            "createdAt": summary_record.created_at.isoformat(),
            "summaryId": summary_record.summary_id
        }

    def ask_chatbot(self, question):
        if not question:
            raise ValidationError("Câu hỏi không được để trống.")

        # 1. Tìm thông tin trong Knowledge Base (ILIKE search đơn giản)
        from app.repositories import KnowledgeBaseRepository
        kb_repo = KnowledgeBaseRepository()
        relevant_docs = kb_repo.search_content(question, limit=3)

        if not relevant_docs:
            # Nếu không tìm thấy gì trong DB, AI sẽ trả lời theo kiểu "không thấy thông tin"
            context = "Không tìm thấy dữ liệu liên quan trong hệ thống."
        else:
            # Gom context
            context_parts = []
            for doc in relevant_docs:
                context_parts.append(f"[{doc.title}]: {doc.content}")
            context = "\n---\n".join(context_parts)

        # 2. Gửi sang AI để xử lý RAG
        answer = AIWrapper.rag_query(context, question)

        return {
            "answer": answer,
            "sources": [doc.title for doc in relevant_docs]
        }

    def detect_toxic(self, text):
        if not text:
            raise ValidationError("Văn bản không được để trống.")

        # 1. Kiểm tra Regex (DLP)
        from app.utils.security import SecurityUtils
        is_sensitive = SecurityUtils.scan_sensitive_content(text)
        if is_sensitive:
            return {
                "isToxic": True,
                "reason": "Phát hiện từ ngữ nhạy cảm/bí mật của công ty (DLP)."
            }

        # 2. Gửi sang AI để phân tích thái độ
        is_toxic, reason = AIWrapper.analyze_toxicity(text)

        return {
            "isToxic": is_toxic,
            "reason": reason
        }
