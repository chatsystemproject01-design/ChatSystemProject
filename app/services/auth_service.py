import secrets
import string
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db, bcrypt
from app.utils.exceptions import ResourceDuplicateError, ResourceNotFoundError, ForbiddenError, UnauthorizedError, ValidationError
from app.repositories import UserRepository, RoleRepository, OTPRepository, IPTrackingRepository
from app.models.role import Role
from app.models.user import User
from app.models.otp import AuthOTP

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.role_repo = RoleRepository()
        self.otp_repo = OTPRepository()
        self.ip_repo = IPTrackingRepository()

    def generate_otp(self, length=6):
        characters = string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))

    def register_user(self, data: dict):
        # 1. Kiểm tra email
        existing_user = self.user_repo.get_by_email(data['email'])
        if existing_user:
            raise ResourceDuplicateError("Email đã tồn tại trong hệ thống.")

        # Thêm Role mặc định là 'Staff' theo yêu cầu người dùng
        from app.constants.enums import RoleEnum
        role_name = RoleEnum.STAFF.value
        role = self.role_repo.get_by_name(role_name)
        if not role:
            # Tạo Role mặc định nếu database trống
            role = self.role_repo.create(role_name=role_name, description="Nhân viên/Thành viên")

        # 2 & 3. Băm mật khẩu (Bcrypt rounds=14 được cấu hình trong Flask-Bcrypt qua BCRYPT_LOG_ROUNDS)
        pw_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')

        try:
            # Transaction (All-or-nothing)
            # 4. Lưu User vào DB (status='pending')
            # Lưu ý số điện thoại ánh xạ từ 'phone'
            new_user = User(
                email=data['email'],
                password_hash=pw_hash,
                full_name=data['fullName'],
                phone_number=data.get('phone'),
                role_id=role.role_id,
                status='pending'
            )
            db.session.add(new_user)
            db.session.flush() # Lấy user_id ngay lập tức

            # 5. Tạo OTP 6 số bằng module secrets
            otp_code = self.generate_otp()
            # Thời hạn 5 phút
            expire_time = datetime.utcnow() + timedelta(minutes=5)
            new_otp = AuthOTP(
                user_id=new_user.user_id,
                otp_code=otp_code,
                expiration_time=expire_time
            )
            db.session.add(new_otp)

            db.session.commit()

            # 6. Gửi Email thật (Rule 7: Bất đồng bộ)
            from app.utils.email import send_otp_email
            send_otp_email(data['email'], otp_code)

            return {
                "userId": str(new_user.user_id)
            }
        except Exception as e:
            db.session.rollback()
            # Bắn lại lỗi sau khi rollback
            raise e

    def login_step_1(self, data: dict, ip_address: str):
        # 1. Kiểm tra IP trong IP_Security_Tracking (Rule: Brute Force Protection)
        ip_track = self.ip_repo.get_by_ip(ip_address)
        if ip_track and ip_track.is_blocked:
            if ip_track.block_until and ip_track.block_until > datetime.utcnow():
                raise ForbiddenError(f"IP này bị tạm khóa. Vui lòng thử lại sau.")
            else:
                # Hết thời gian block, reset để thử lại
                ip_track.is_blocked = False
                ip_track.failed_count = 0
                db.session.commit()

        # 2. Tìm User theo Email
        user = self.user_repo.get_by_email(data['email'])
        
        # 3. Kiểm tra User tồn tại và Pass đúng (Bcrypt)
        if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
            # Logic tăng failed count (Rule: Security)
            if not ip_track:
                self.ip_repo.create(ip_address=ip_address, failed_count=1, last_failed_at=datetime.utcnow())
            else:
                ip_track.failed_count += 1
                ip_track.last_failed_at = datetime.utcnow()
                if ip_track.failed_count >= 5:
                    ip_track.is_blocked = True
                    ip_track.block_until = datetime.utcnow() + timedelta(minutes=15)
                db.session.commit()
            raise UnauthorizedError("Email hoặc mật khẩu không chính xác.")

        # 4. Đăng nhập đúng -> Reset IP Tracking cho IP này
        if ip_track:
            ip_track.failed_count = 0
            ip_track.is_blocked = False
            db.session.commit()

        # 5. Tạo OTP 2FA
        otp_code = self.generate_otp()
        expire_time = datetime.utcnow() + timedelta(minutes=5)
        new_otp = AuthOTP(
            user_id=user.user_id,
            otp_code=otp_code,
            expiration_time=expire_time
        )
        db.session.add(new_otp)
        db.session.commit()

        # 6. Gửi Email OTP (Rule 7: Bất đồng bộ)
        from app.utils.email import send_otp_email
        send_otp_email(user.email, otp_code)

        return {"require2FA": True}

    def verify_2fa(self, data: dict):
        # 1. Tìm User
        user = self.user_repo.get_by_email(data['email'])
        if not user:
            raise ResourceNotFoundError("Người dùng không tồn tại.")

        # 2. Tìm OTP mới nhất (Rule: Security)
        latest_otp = self.otp_repo.get_latest_otp(user.user_id)
        
        if not latest_otp or latest_otp.otp_code != data['otpCode']:
            raise ValidationError("Mã OTP không chính xác.")

        # 3. Kiểm tra hết hạn
        if latest_otp.expiration_time < datetime.utcnow():
            raise ValidationError("Mã OTP đã hết hạn.")

        try:
            # 4. Thành công -> Đánh dấu đã dùng và activate user
            latest_otp.is_used = True
            user.status = 'active'
            user.last_seen = datetime.utcnow()
            
            db.session.commit()

            # 5. Tạo JWT Token (Access + Refresh) - Rule 4
            additional_claims = {"role": user.role.role_name}
            access_token = create_access_token(identity=str(user.user_id), additional_claims=additional_claims)
            refresh_token = create_refresh_token(identity=str(user.user_id))

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "userId": str(user.user_id),
                    "email": user.email,
                    "fullName": user.full_name,
                    "role": user.role.role_name if user.role else None
                }
            }
        except Exception as e:
            db.session.rollback()
            raise e

    def resend_otp(self, email: str):
        # 1. Tìm User
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ResourceNotFoundError("Người dùng không tồn tại.")

        try:
            # 2. Vô hiệu hóa mã cũ
            self.otp_repo.invalidate_all_user_otps(user.user_id)
            
            # 3. Tạo mã mới 6 số
            otp_code = self.generate_otp()
            expire_time = datetime.utcnow() + timedelta(minutes=5)
            new_otp = AuthOTP(
                user_id=user.user_id,
                otp_code=otp_code,
                expiration_time=expire_time
            )
            db.session.add(new_otp)
            db.session.commit()

            # 4. Gửi Email OTP (Rule 7: Bất đồng bộ)
            from app.utils.email import send_otp_email
            send_otp_email(user.email, otp_code)

            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def forgot_password(self, email: str):
        # 1. Tìm User
        user = self.user_repo.get_by_email(email)
        
        # Rule: Bảo mật - không xác nhận email có thật hay không
        if not user:
            return True

        try:
            # 2. Vô hiệu hóa mã cũ
            self.otp_repo.invalidate_all_user_otps(user.user_id)
            
            # 3. Tạo mã reset mới (thời hạn 10 phút)
            otp_code = self.generate_otp()
            expire_time = datetime.utcnow() + timedelta(minutes=10)
            new_otp = AuthOTP(
                user_id=user.user_id,
                otp_code=otp_code,
                expiration_time=expire_time
            )
            db.session.add(new_otp)
            db.session.commit()

            # 4. Gửi Email (Rule 7: Bất đồng bộ)
            from app.utils.email import send_otp_email
            send_otp_email(user.email, otp_code)

            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def reset_password(self, data: dict):
        # 1. Tìm User
        user = self.user_repo.get_by_email(data['email'])
        if not user:
            raise ResourceNotFoundError("Người dùng không tồn tại.")

        # 2. Kiểm tra OTP
        latest_otp = self.otp_repo.get_latest_otp(user.user_id)
        if not latest_otp or latest_otp.otp_code != data['otpCode']:
            raise ValidationError("Mã OTP không chính xác.")

        if latest_otp.expiration_time < datetime.utcnow():
            raise ValidationError("Mã OTP đã hết hạn.")

        try:
            # 3. Băm mật khẩu mới
            new_hash = bcrypt.generate_password_hash(data['newPassword']).decode('utf-8')
            
            # 4. Update User và vô hiệu hóa OTP
            user.password_hash = new_hash
            latest_otp.is_used = True
            db.session.commit()

            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def change_password(self, user_id: str, data: dict):
        # 1. Tìm User
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("Người dùng không tồn tại.")

        # 2. Kiểm tra mật khẩu cũ (Bcrypt)
        if not bcrypt.check_password_hash(user.password_hash, data['oldPassword']):
            raise UnauthorizedError("Mật khẩu cũ không chính xác.")

        try:
            # 3. Băm mật khẩu mới
            new_hash = bcrypt.generate_password_hash(data['newPassword']).decode('utf-8')
            
            # 4. Update
            user.password_hash = new_hash
            db.session.commit()

            return True
        except Exception as e:
            db.session.rollback()
            raise e
