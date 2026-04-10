from app.extensions import db
from sqlalchemy.orm import Session

class BaseRepository:
    def __init__(self, model):
        self.model = model

    def get_by_id(self, id):
        return db.session.get(self.model, id)

    def get_all(self, offset=0, limit=100):
        return self.model.query.offset(offset).limit(limit).all()

    def create(self, **kwargs):
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, id, **kwargs):
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            db.session.commit()
        return instance

    def delete(self, id):
        instance = self.get_by_id(id)
        if instance:
            db.session.delete(instance)
            db.session.commit()
            return True
        return False

    def save(self, instance):
        db.session.add(instance)
        db.session.commit()
        return instance
