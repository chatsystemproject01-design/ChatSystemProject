from app.models.user import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, email):
        return self.model.query.filter_by(email=email, is_deleted=False).first()

    def get_by_phone(self, phone):
        return self.model.query.filter_by(phone_number=phone, is_deleted=False).first()

    def search_users(self, query, current_user_id):
        return self.model.query.filter(
            (self.model.email.ilike(f"%{query}%")) | 
            (self.model.full_name.ilike(f"%{query}%"))
        ).filter(self.model.user_id != current_user_id, self.model.is_deleted == False).all()
