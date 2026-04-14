from app.repositories import ConversationRepository, ParticipantRepository, UserRepository, MessageRepository, BlockedUserRepository
from app.utils.crypto import CryptoUtils
from app.utils.security import SecurityUtils
from app.utils.exceptions import ValidationError, ResourceNotFoundError, ForbiddenError
from app.extensions import db
from datetime import datetime, timedelta
from app.models.conversation import Conversation
from app.models.participant import ConversationParticipant
from app.models.message import Message
from app.models.message_status import MessageStatus

class ConversationService:
    def __init__(self):
        self.conv_repo = ConversationRepository()
        self.participant_repo = ParticipantRepository()
        self.user_repo = UserRepository()
        self.message_repo = MessageRepository()
        self.blocked_repo = BlockedUserRepository()

    def create_conversation(self, creator_id, data):
        is_group = data.get('isGroup', False)
        
        if not is_group:
            # Chat cá nhân (1-1)
            target_user_id = data.get('targetUserId')
            if not target_user_id:
                raise ValidationError("Cần targetUserId cho cuộc trò chuyện cá nhân.")
            
            if str(creator_id) == str(target_user_id):
                raise ValidationError("Bạn không thể tạo cuộc trò chuyện 1-1 với chính mình.")

            # Kiểm tra user đích có tồn tại không
            target_user = self.user_repo.get_by_id(target_user_id)
            if not target_user:
                raise ResourceNotFoundError("Người dùng không tồn tại.")

            # Kiểm tra xem đã có hội thoại 1-1 chưa
            existing = self._find_existing_private_conv(creator_id, target_user_id)
            if existing:
                return {"conversationId": existing.conversation_id}
            
            # Tạo mới
            conv = self.conv_repo.create(is_group=False, created_by=creator_id)
            self.participant_repo.create(conversation_id=conv.conversation_id, user_id=creator_id, role_in_group='owner')
            self.participant_repo.create(conversation_id=conv.conversation_id, user_id=target_user_id, role_in_group='member')
            
            return {"conversationId": conv.conversation_id}
        else:
            # Chat nhóm
            name = data.get('conversationName')
            member_ids = data.get('memberIds', [])
            
            if not name:
                raise ValidationError("Tên nhóm không được để trống.")
            if not member_ids:
                raise ValidationError("Danh sách thành viên không được để trống.")
            
            conv = self.conv_repo.create(is_group=True, conversation_name=name, created_by=creator_id)
            
            # Thêm người tạo làm Chủ nhóm (Owner)
            self.participant_repo.create(conversation_id=conv.conversation_id, user_id=creator_id, role_in_group='owner')
            
            # Thêm các thành viên khác
            for m_id in member_ids:
                if str(m_id) != str(creator_id):
                    # Kiểm tra user tồn tại trước khi thêm
                    user = self.user_repo.get_by_id(m_id)
                    if user:
                        self.participant_repo.create(conversation_id=conv.conversation_id, user_id=m_id, role_in_group='member')
            
            return {"conversationId": conv.conversation_id}

    def _find_existing_private_conv(self, user1_id, user2_id):
        # Truy vấn tìm cuộc hội thoại 1-1 mà cả 2 đều là thành viên
        # Sử dụng subquery để tìm ID conversation chung
        sub1 = db.session.query(ConversationParticipant.conversation_id).filter(ConversationParticipant.user_id == user1_id).subquery()
        sub2 = db.session.query(ConversationParticipant.conversation_id).filter(ConversationParticipant.user_id == user2_id).subquery()
        
        conv = Conversation.query.join(sub1, Conversation.conversation_id == sub1.c.conversation_id)\
                                 .join(sub2, Conversation.conversation_id == sub2.c.conversation_id)\
                                 .filter(Conversation.is_group == False).first()
        return conv

    def get_user_conversations(self, user_id):
        # 1. Lấy danh sách conversation mà user tham gia
        conversations = self.conv_repo.get_user_conversations(user_id)
        
        result = []
        for conv in conversations:
            # 2. Xác định tên/ảnh hội thoai
            name = conv.conversation_name
            avatar = None
            
            if not conv.is_group:
                # Tìm participant còn lại (1-1 chat)
                other_participant = next((p for p in conv.participants if str(p.user_id) != str(user_id)), None)
                if other_participant:
                    name = other_participant.user.full_name
                    avatar = other_participant.user.avatar_url
            
            # 3. Lấy tin nhắn mới nhất
            last_msg = db.session.query(Message).filter(
                Message.conversation_id == conv.conversation_id, 
                Message.is_deleted == False
            ).order_by(Message.created_at.desc()).first()
            
            # 4. Đếm số tin nhắn chưa đọc
            unread_count = db.session.query(MessageStatus).join(Message).filter(
                Message.conversation_id == conv.conversation_id,
                MessageStatus.user_id == user_id,
                MessageStatus.status != 'seen'
            ).count()
            
            result.append({
                "conversationId": conv.conversation_id,
                "name": name,
                "avatarUrl": avatar,
                "lastMessage": last_msg.message_content if last_msg else None,
                "lastMessageTime": last_msg.created_at.isoformat() if last_msg else None,
                "unreadCount": unread_count,
                "isGroup": conv.is_group
            })
            
        return result

    def update_conversation(self, user_id, conversation_id, data):
        # 1. Kiểm tra tồn tại
        conv = self.conv_repo.get_by_id(conversation_id)
        if not conv or conv.is_deleted:
            raise ResourceNotFoundError("Không tìm thấy cuộc hội thoại.")

        if not conv.is_group:
            raise ValidationError("Chỉ có thể cập nhật thông tin cho nhóm.")

        # 2. Kiểm tra quyền (Admin/Owner)
        participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
        if not participant or participant.role_in_group not in ['admin', 'owner']:
            raise ForbiddenError("Bạn không có quyền cập nhật thông tin nhóm.")

        # 3. Chuẩn bị dữ liệu cập nhật
        update_data = {}
        if 'conversationName' in data and data['conversationName']:
            update_data['conversation_name'] = data['conversationName']
        if 'avatarUrl' in data:
            update_data['avatar_url'] = data['avatarUrl']

        if not update_data:
            return conv

        # 4. Cập nhật
        return self.conv_repo.update(conversation_id, **update_data)

    def get_conversation_detail(self, user_id, conversation_id):
        # 1. Kiểm tra quyền truy cập (Người dùng có trong bảng Participants của ID này không?)
        participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
        if not participant:
            raise ForbiddenError("Bạn không có quyền truy cập thông tin phòng chat này.")

        # 2. Lấy dữ liệu từ bảng conversations
        conv = self.conv_repo.get_by_id(conversation_id)
        if not conv or conv.is_deleted:
            raise ResourceNotFoundError("Không tìm thấy cuộc hội thoại.")

        # 3. Chuẩn bị dữ liệu trả về
        name = conv.conversation_name
        avatar = conv.avatar_url
        
        if not conv.is_group:
            # Lấy thông tin người đối diện
            other_p = next((p for p in conv.participants if str(p.user_id) != str(user_id)), None)
            if other_p:
                name = other_p.user.full_name
                avatar = other_p.user.avatar_url

        # 4. Lấy tin nhắn ghim (Pinned Message)
        pinned_msg = db.session.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_pinned == True,
            Message.is_deleted == False
        ).order_by(Message.updated_at.desc()).first()

        pinned_data = None
        if pinned_msg:
            pinned_data = {
                "messageId": pinned_msg.message_id,
                "content": CryptoUtils.decrypt(pinned_msg.message_content),
                "senderName": pinned_msg.sender.full_name
            }

        return {
            "conversationId": conv.conversation_id,
            "conversationName": name,
            "avatarUrl": avatar,
            "isGroup": conv.is_group,
            "createdBy": conv.created_by,
            "createdAt": conv.created_at.isoformat(),
            "roleInGroup": participant.role_in_group,
            "pinnedMessage": pinned_data
        }

    def delete_conversation(self, user_id, conversation_id):
        # 1. Kiểm tra tồn tại
        conv = self.conv_repo.get_by_id(conversation_id)
        if not conv or conv.is_deleted:
            raise ResourceNotFoundError("Không tìm thấy cuộc hội thoại.")

        # 2. Kiểm tra quyền sở hữu (Admin/Owner)
        participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
        if not participant or participant.role_in_group not in ['admin', 'owner']:
            raise ForbiddenError("Bạn không có quyền xóa hội thoại này.")

        # 3. Cập nhật trường is_deleted = True
        return self.conv_repo.update(conversation_id, is_deleted=True)

    def get_conversation_members(self, user_id, conversation_id):
        # 1. Kiểm tra quyền truy cập (User phải thuộc nhóm đó)
        participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
        if not participant:
            raise ForbiddenError("Bạn không có quyền xem danh sách thành viên của phòng chat này.")

        # 2. Lấy danh sách thành viên
        members = ConversationParticipant.query.filter_by(conversation_id=conversation_id).all()
        
        return [
            {
                "userId": str(m.user_id),
                "fullName": m.user.full_name,
                "avatarUrl": m.user.avatar_url,
                "roleInGroup": m.role_in_group,
                "joinedAt": m.joined_at.isoformat()
            } for m in members
        ]

    def add_member(self, admin_id, conversation_id, new_member_id):
        # 1. Kiểm tra phòng chat tồn tại và là nhóm
        conv = self.conv_repo.get_by_id(conversation_id)
        if not conv or not conv.is_group or conv.is_deleted:
            raise ValidationError("Phòng chat không tồn tại hoặc không phải là nhóm.")

        # 2. Kiểm tra quyền Admin/Owner của người thực hiện
        admin_p = self.participant_repo.get_by_conversation_and_user(conversation_id, admin_id)
        if not admin_p or admin_p.role_in_group not in ['admin', 'owner']:
            raise ForbiddenError("Chỉ Admin/Owner được phép thêm thành viên.")

        # 3. Kiểm tra user mới có tồn tại không
        new_user = self.user_repo.get_by_id(new_member_id)
        if not new_user:
            raise ResourceNotFoundError("Người dùng muốn thêm không tồn tại.")

        # 4. Kiểm tra user đã ở trong nhóm chưa
        existing_p = self.participant_repo.get_by_conversation_and_user(conversation_id, new_member_id)
        if existing_p:
            raise ValidationError("Người dùng này đã là thành viên của nhóm.")

        # 5. Thêm thành viên
        return self.participant_repo.create(
            conversation_id=conversation_id,
            user_id=new_member_id,
            role_in_group='member'
        )

    def remove_member(self, admin_id, conversation_id, member_id_to_remove):
        # 1. Kiểm tra phòng chat
        conv = self.conv_repo.get_by_id(conversation_id)
        if not conv or not conv.is_group:
            raise ValidationError("Phòng chat không tồn tại hoặc không phải là nhóm.")

        # 2. Kiểm tra quyền của người xóa (Phải là Admin/Owner)
        admin_p = self.participant_repo.get_by_conversation_and_user(conversation_id, admin_id)
        if not admin_p or admin_p.role_in_group not in ['admin', 'owner']:
            raise ForbiddenError("Chỉ Admin/Owner được phép xóa thành viên.")

        # 3. Kiểm tra thông tin người bị xóa
        target_p = self.participant_repo.get_by_conversation_and_user(conversation_id, member_id_to_remove)
        if not target_p:
            raise ResourceNotFoundError("Thành viên cần xóa không có trong nhóm.")

        # 4. Ràng buộc: Không thể xóa Owner
        if target_p.role_in_group == 'owner':
            raise ForbiddenError("Không thể xóa chủ nhóm.")
        
        # Không thể tự xóa mình qua API này
        if str(admin_id) == str(member_id_to_remove):
             raise ValidationError("Sử dụng endpoint 'leave' để rời nhóm.")

        # 5. Thực hiện xóa
        db.session.delete(target_p)
        db.session.commit()
        return True

    def leave_group(self, user_id, conversation_id):
        # 1. Kiểm tra tư cách thành viên
        participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
        if not participant:
            raise ValidationError("Bạn không phải là thành viên của nhóm này.")

        # 2. Ràng buộc Owner duy nhất
        if participant.role_in_group == 'owner':
            count = ConversationParticipant.query.filter_by(conversation_id=conversation_id).count()
            if count > 1:
                raise ValidationError("Vui lòng chuyển quyền trưởng nhóm trước khi rời đi.")
        
        # 3. Xóa bản ghi
        db.session.delete(participant)
        db.session.commit()
        return True

    def transfer_owner(self, current_owner_id, conversation_id, new_owner_id):
        # 1. Kiểm tra phòng chat
        conv = self.conv_repo.get_by_id(conversation_id)
        if not conv or not conv.is_group:
            raise ValidationError("Phòng chat không tồn tại hoặc không phải là nhóm.")

        # 2. Kiểm tra quyền của người thực hiện (Phải là Owner)
        current_p = self.participant_repo.get_by_conversation_and_user(conversation_id, current_owner_id)
        if not current_p or current_p.role_in_group != 'owner':
            raise ForbiddenError("Chỉ Chủ nhóm (Owner) mới được chuyển quyền trưởng nhóm.")

        # 3. Kiểm tra người nhận quyền
        new_p = self.participant_repo.get_by_conversation_and_user(conversation_id, new_owner_id)
        if not new_p:
            raise ValidationError("Người nhận quyền phải là thành viên trong nhóm.")

        if str(current_owner_id) == str(new_owner_id):
            raise ValidationError("Bạn đã là Chủ nhóm.")

        # 4. Thực hiện chuyển quyền
        new_p.role_in_group = 'owner'
        current_p.role_in_group = 'admin' # Hạ cấp xuống admin

        db.session.commit()
        return True

    def get_chat_history(self, user_id, conversation_id, offset=0, limit=50):
        # 1. Kiểm tra tư cách thành viên
        participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
        if not participant:
            raise ForbiddenError("Bạn không có quyền xem lịch sử tin nhắn của hội thoại này.")

        # 2. Truy vấn danh sách tin nhắn
        messages = self.message_repo.get_conversation_messages(conversation_id, offset, limit)

        # 3. Giải mã và format dữ liệu
        result = []
        for msg in messages:
            decrypted_content = CryptoUtils.decrypt(msg.message_content)
            msg_data = {
                "messageId": msg.message_id,
                "content": decrypted_content,
                "senderId": str(msg.sender_id),
                "messageType": msg.message_type,
                "createdAt": msg.created_at.isoformat()
            }
            
            # Đính kèm thông tin media nếu có
            if msg.message_type in ['voice', 'media'] and msg.attachments:
                attachment = msg.attachments[0]
                if msg.message_type == 'voice':
                    msg_data["audioUrl"] = attachment.file_url
                    msg_data["duration"] = attachment.duration
                else:
                    msg_data["fileUrl"] = attachment.file_url
                    
            result.append(msg_data)

        return result

    def send_message(self, user_id, data):
        conversation_id = data.get('conversationId')
        content = data.get('messageContent')
        msg_type = data.get('messageType', 'text')

        # 1. Kiểm tra tồn tại hội thoại
        conv = self.conv_repo.get_by_id(conversation_id)
        if not conv or conv.is_deleted:
            raise ResourceNotFoundError("Không tìm thấy cuộc hội thoại.")

        # 2. Kiểm tra tư cách thành viên
        participant = self.participant_repo.get_by_conversation_and_user(conversation_id, user_id)
        if not participant:
            raise ForbiddenError("Bạn không phải là thành viên của cuộc hội thoại này.")

        # 3. Quét DLP (Regex) để phát hiện từ ngữ nhạy cảm
        from app.utils.security import SecurityUtils
        is_sensitive = SecurityUtils.scan_sensitive_content(content)
        if is_sensitive:
            raise ValidationError("Tin nhắn chứa từ ngữ nhạy cảm hoặc vi phạm chính sách bảo mật (DLP).")

        # 4. Quét AI Toxicity (Phân tích thái độ)
        from app.services.ai_service import AIService
        ai_service = AIService()
        toxic_result = ai_service.detect_toxic(content)
        if toxic_result['isToxic']:
            raise ValidationError(f"Tin nhắn bị chặn: {toxic_result['reason']}")

        # 5. Mã hóa AES-128-CBC trước khi lưu DB
        from app.utils.crypto import CryptoUtils
        encrypted_content = CryptoUtils.encrypt(content)

        # 6. Lưu vào database
        msg = self.message_repo.create(
            conversation_id=conversation_id,
            sender_id=user_id,
            message_content=encrypted_content,
            message_type=msg_type,
            is_toxic=False # Nếu đến đây thì đã an toàn
        )

        # 6. Trigger Socket (Thông báo realtime cho các thành viên khác)
        from app.extensions import socketio
        socketio.emit('new_message', {
            "messageId": msg.message_id,
            "conversationId": conversation_id,
            "senderId": str(user_id),
            "content": content, 
            "createdAt": msg.created_at.isoformat()
        }, room=f"conversation_{conversation_id}")

        # 7. Tự động tắt trạng thái "đang nhập" sau khi gửi tin nhắn
        socketio.emit('user_typing', {
            'conversationId': conversation_id,
            'userId': str(user_id),
            'isTyping': False
        }, room=f"conversation_{conversation_id}")

        return {"messageId": msg.message_id}

    def edit_message(self, user_id, message_id, new_content):
        # 1. Tìm tin nhắn
        msg = self.message_repo.get_by_id(message_id)
        if not msg or msg.is_deleted:
            raise ResourceNotFoundError("Không tìm thấy tin nhắn.")

        # 2. Validate quyền sở hữu (Chỉ người gửi mới được sửa)
        if str(msg.sender_id) != str(user_id):
            raise ForbiddenError("Bạn không có quyền chỉnh sửa tin nhắn này.")

        # 3. Kiểm tra thời gian (Ví dụ: 15 phút)
        time_diff = datetime.utcnow() - msg.created_at
        if time_diff > timedelta(minutes=15):
            raise ValidationError("Đã quá thời gian cho phép chỉnh sửa tin nhắn (tối đa 15 phút).")

        # 4. Quét DLP và Mã hóa mới
        is_toxic = SecurityUtils.scan_sensitive_content(new_content)
        encrypted_content = CryptoUtils.encrypt(new_content)

        # 5. Cập nhật
        return self.message_repo.update(message_id, 
                                        message_content=encrypted_content, 
                                        is_toxic=is_toxic)

    def delete_message(self, user_id, message_id):
        # 1. Tìm tin nhắn
        msg = self.message_repo.get_by_id(message_id)
        if not msg or msg.is_deleted:
            raise ResourceNotFoundError("Không tìm thấy tin nhắn.")

        # 2. Kiểm tra quyền xóa
        # Quyền 1: Là người gửi
        if str(msg.sender_id) == str(user_id):
            can_delete = True
        else:
            # Quyền 2: Là Admin/Owner của phòng chat
            participant = self.participant_repo.get_by_conversation_and_user(msg.conversation_id, user_id)
            if participant and participant.role_in_group in ['admin', 'owner']:
                can_delete = True
            else:
                can_delete = False

        if not can_delete:
            raise ForbiddenError("Bạn không có quyền xóa tin nhắn này.")

        # 3. Thực hiện xóa mềm
        return self.message_repo.update(message_id, is_deleted=True)

    def pin_message(self, user_id, message_id, is_pinned=True):
        # 1. Tìm tin nhắn
        msg = self.message_repo.get_by_id(message_id)
        if not msg or msg.is_deleted:
            raise ResourceNotFoundError("Không tìm thấy tin nhắn.")

        # 2. Kiểm tra quyền ghim (Chỉ Admin/Owner phòng chat)
        participant = self.participant_repo.get_by_conversation_and_user(msg.conversation_id, user_id)
        if not participant or participant.role_in_group not in ['admin', 'owner']:
            raise ForbiddenError("Chỉ Admin hoặc Chủ phòng mới có quyền ghim tin nhắn.")

        # 3. Cập nhật trạng thái ghim
        return self.message_repo.update(message_id, is_pinned=is_pinned)

    def forward_message(self, user_id, data):
        source_id = data.get('sourceMessageId')
        target_ids = data.get('targetConversationIds', [])

        if not target_ids:
            raise ValidationError("Danh sách cuộc hội thoại đích không được trống.")

        # 1. Lấy tin nhắn gốc
        msg = self.message_repo.get_by_id(source_id)
        if not msg or msg.is_deleted:
            raise ResourceNotFoundError("Không tìm thấy tin nhắn gốc.")

        # 2. Giải mã nội dung
        from app.utils.crypto import CryptoUtils
        decrypted_content = CryptoUtils.decrypt(msg.message_content)

        # 3. Gửi sang từng cuộc hội thoại đích
        for tid in target_ids:
            # Tái sử dụng logic send_message để đảm bảo DLP và mã hóa đúng chuẩn
            try:
                self.send_message(user_id, {
                    "conversationId": tid,
                    "messageContent": decrypted_content,
                    "messageType": msg.message_type
                })
            except Exception as e:
                # Log lỗi cho từng cuộc hội thoại nếu cần, ở đây ta tiếp tục với các ID khác
                continue

        return True






