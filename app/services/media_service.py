from app.repositories import FileAttachmentRepository, ParticipantRepository, MessageRepository, ConversationRepository
from app.utils.media_storage import MediaStorage
from app.utils.exceptions import ValidationError, ApplicationError, ForbiddenError, ResourceNotFoundError
from app.utils.crypto import CryptoUtils
from app.extensions import db

class MediaService:
    def __init__(self):
        self.file_repo = FileAttachmentRepository()
        self.participant_repo = ParticipantRepository()
        self.message_repo = MessageRepository()
        self.conv_repo = ConversationRepository()

    def upload_media(self, user_id, file_obj, conversation_id=None):
        """
        Quy trình 1 bước: Upload tệp tin và tự động gửi tin nhắn nếu có conversation_id.
        """
        # 1. Nếu có conversation_id, kiểm tra quyền trước khi upload tốn tài nguyên
        if conversation_id:
            conv = self.conv_repo.get_by_id(conversation_id)
            if not conv or conv.is_deleted:
                raise ResourceNotFoundError("Không tìm thấy cuộc hội thoại.")
            
            participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
            if not participant:
                raise ForbiddenError("Bạn không phải là thành viên của cuộc hội thoại này.")

        # 2. Validate file
        is_valid, kind_or_error = MediaStorage.validate_file(file_obj)
        if not is_valid:
            raise ValidationError(kind_or_error)
        
        kind = kind_or_error # filetype result

        # 3. Upload lên Supabase
        try:
            filename = file_obj.filename
            upload_result = MediaStorage.upload_file(file_obj, filename)
        except Exception as e:
            raise ApplicationError(f"Không thể upload tệp tin: {str(e)}")

        # 4. Nếu có conversation_id, tạo tin nhắn tự động
        message_id = None
        if conversation_id:
            # Mã hóa URL để lưu vào message_content (cho đồng bộ logic chat history)
            display_content = f"Sent a file: {filename}"
            encrypted_url = CryptoUtils.encrypt(display_content)
            
            msg = self.message_repo.create(
                conversation_id=conversation_id,
                sender_id=user_id,
                message_content=encrypted_url,
                message_type="media",
                is_toxic=False # Đã qua Magic Bytes check
            )
            message_id = msg.message_id

            # Trigger Socket REALTIME
            try:
                from app.extensions import socketio
                socketio.emit('new_message', {
                    "messageId": msg.message_id,
                    "conversationId": conversation_id,
                    "senderId": str(user_id),
                    "content": display_content,
                    "messageType": "media",
                    "fileUrl": upload_result['url'],
                    "createdAt": msg.created_at.isoformat()
                }, room=f"conversation_{conversation_id}")
            except:
                pass # Bỏ qua nếu socket lỗi, ưu tiên HTTP success

        # 5. Lưu bản ghi vào bảng files_attachments
        file_record = self.file_repo.create(
            message_id=message_id, # Link tới tin nhắn vừa tạo (nếu có)
            file_name=filename,
            file_url=upload_result['url'],
            mime_type=kind.mime,
            file_size=upload_result['size'],
            magic_bytes_status="validated",
            is_secure=True
        )

        return {
            "fileId": file_record.file_id,
            "url": upload_result['url'],
            "messageId": message_id
        }


    def get_conversation_media(self, user_id, conversation_id):
        # 1. Kiểm tra tư cách thành viên
        participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
        if not participant:
            raise ForbiddenError("Bạn không phải là thành viên của cuộc hội thoại này.")

        # 2. Truy vấn danh sách tệp tin
        attachments = self.file_repo.get_by_conversation(conversation_id)

        # 3. Format dữ liệu trả về
        return [
            {
                "fileName": attr.file_name,
                "url": attr.file_url,
                "createdAt": attr.created_at.isoformat()
            } for attr in attachments
        ]
