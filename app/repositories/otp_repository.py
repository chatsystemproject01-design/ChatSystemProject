from app.models.otp import AuthOTP
from app.repositories.base_repository import BaseRepository

class OTPRepository(BaseRepository):
    def __init__(self):
        super().__init__(AuthOTP)

    def get_latest_otp(self, user_id):
        return self.model.query.filter_by(user_id=user_id, is_used=False)\
            .order_by(self.model.created_at.desc()).first()

    def invalidate_all_user_otps(self, user_id):
        self.model.query.filter_by(user_id=user_id, is_used=False).update({"is_used": True})
