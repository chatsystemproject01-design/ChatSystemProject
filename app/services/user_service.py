from app.repositories import UserRepository, ContactRepository, BlockedUserRepository, ReportRepository, MessageRepository
from app.utils.exceptions import ResourceNotFoundError, ResourceDuplicateError, ValidationError
from datetime import datetime

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.contact_repo = ContactRepository()
        self.blocked_repo = BlockedUserRepository()
        self.report_repo = ReportRepository()
        self.message_repo = MessageRepository()

    def get_my_profile(self, user_id: str):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("Không tìm thấy thông tin người dùng.")

        return {
            "userId": str(user.user_id),
            "fullName": user.full_name,
            "email": user.email,
            "phoneNumber": user.phone_number,
            "dateOfBirth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "avatarUrl": user.avatar_url,
            "position": user.position,
            "role": user.role.role_name if user.role else None,
            "status": user.status,
            "lastSeen": user.last_seen.isoformat() if user.last_seen else None,
            "createdAt": user.created_at.isoformat() if user.created_at else None
        }

    def get_contacts(self, user_id: str):
        contacts = self.contact_repo.get_user_contacts(user_id)
        
        result = []
        for contact in contacts:
            colleague = contact.colleague
            if colleague and not colleague.is_deleted:
                result.append({
                    "userId": str(colleague.user_id),
                    "fullName": colleague.full_name,
                    "avatarUrl": colleague.avatar_url,
                    "status": colleague.status,
                    "lastSeen": colleague.last_seen.isoformat() if colleague.last_seen else None,
                    "position": colleague.position
                })
        
        return result

    def search_users(self, query: str, current_user_id: str):
        users = self.user_repo.search_users(query, current_user_id)
        
        return [
            {
                "userId": str(user.user_id),
                "fullName": user.full_name,
                "email": user.email,
                "avatarUrl": user.avatar_url,
                "position": user.position,
                "status": user.status
            } for user in users
        ]

    def add_contact(self, user_id: str, colleague_id: str):
        if str(user_id) == str(colleague_id):
            raise ValidationError("Bạn không thể thêm chính mình vào danh sách liên hệ.")
        
        # 1. Kiểm tra colleague có tồn tại không
        colleague = self.user_repo.get_by_id(colleague_id)
        if not colleague:
            raise ResourceNotFoundError("Đồng nghiệp không tồn tại.")
        
        # 2. Kiểm tra đã tồn tại chưa
        existing = self.contact_repo.model.query.filter_by(user_id=user_id, colleague_id=colleague_id).first()
        if existing:
            raise ResourceDuplicateError("Người này đã có trong danh sách liên hệ của bạn.")
        
        # 3. Thêm mới
        self.contact_repo.create(user_id=user_id, colleague_id=colleague_id)
        return True

    def remove_contact(self, user_id: str, colleague_id: str):
        success = self.contact_repo.remove_contact(user_id, colleague_id)
        if not success:
            raise ResourceNotFoundError("Không tìm thấy liên hệ này trong danh sách của bạn.")
        return True

    def block_user(self, user_id: str, target_user_id: str):
        if str(user_id) == str(target_user_id):
            raise ValidationError("Bạn không thể chặn chính mình.")
        
        # 1. Kiểm tra target user tồn tại
        target_user = self.user_repo.get_by_id(target_user_id)
        if not target_user:
            raise ResourceNotFoundError("Người dùng cần chặn không tồn tại.")
        
        # 2. Thêm vào bảng BlockedUsers
        if not self.blocked_repo.is_blocked(user_id, target_user_id):
            self.blocked_repo.create(user_id=user_id, blocked_user_id=target_user_id)
        
        # 3. Hủy mối quan hệ trong contacts (nếu có)
        self.contact_repo.remove_contact(user_id, target_user_id)
        
        return True

    def update_profile(self, user_id: str, data: dict):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("Người dùng không tồn tại.")
        
        update_data = {}
        if 'fullName' in data and data['fullName'] is not None:
            update_data['full_name'] = data['fullName']
        if 'phoneNumber' in data and data['phoneNumber'] is not None:
            update_data['phone_number'] = data['phoneNumber']
        if 'dateOfBirth' in data and data['dateOfBirth'] is not None:
            try:
                update_data['date_of_birth'] = datetime.strptime(data['dateOfBirth'], '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError("Ngày sinh không hợp lệ. Định dạng yêu cầu: YYYY-MM-DD.")
        if 'position' in data and data['position'] is not None:
            update_data['position'] = data['position']
        if 'avatarUrl' in data and data['avatarUrl'] is not None:
            update_data['avatar_url'] = data['avatarUrl']
            
        if not update_data:
            return True
            
        self.user_repo.update(user_id, **update_data)
        return True

    def create_report(self, reporter_id: str, data: dict):
        reported_user_id = data.get('reportedUserId')
        reported_message_id = data.get('reportedMessageId')
        reason_type = data.get('reasonType')
        description = data.get('description')

        if not reported_user_id and not reported_message_id:
            raise ValidationError("Phải cung cấp ít nhất một đối tượng bị báo cáo (Người dùng hoặc Tin nhắn).")

        # 1. Báo cáo chính mình
        if reported_user_id and str(reporter_id) == str(reported_user_id):
            raise ValidationError("Bạn không thể tự báo cáo chính mình.")

        # 2. Kiểm tra tồn tại đối tượng
        if reported_user_id:
            reported_user = self.user_repo.get_by_id(reported_user_id)
            if not reported_user:
                raise ResourceNotFoundError("Người dùng bị báo cáo không tồn tại.")
        
        if reported_message_id:
            reported_msg = self.message_repo.get_by_id(reported_message_id)
            if not reported_msg:
                raise ResourceNotFoundError("Tin nhắn bị báo cáo không tồn tại.")

        # 3. Tạo báo cáo
        report = self.report_repo.create(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            reported_message_id=reported_message_id,
            reason_type=reason_type,
            description=description,
            status='pending'
        )

        return report.report_id

    def get_my_reports(self, user_id: str):
        reports = self.report_repo.get_by_reporter(user_id)
        
        return [
            {
                "reportId": r.report_id,
                "reportedUserId": str(r.reported_user_id) if r.reported_user_id else None,
                "reportedMessageId": r.reported_message_id,
                "reasonType": r.reason_type,
                "status": r.status,
                "adminNote": r.admin_note,
                "createdAt": r.created_at.isoformat()
            } for r in reports
        ]

    def get_report_reasons(self):
        return [
            "Spam (Tin nhắn rác)",
            "Toxic (Ngôn ngữ độc hại)",
            "Harassment (Quấy rối)",
            "Data Leak (Lộ bí mật công ty)",
            "Scam (Lừa đảo)",
            "Other (Lý do khác)"
        ]
