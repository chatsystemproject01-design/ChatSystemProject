from app.extensions import db

class SystemConfig(db.Model):
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_registration_enabled = db.Column(db.Boolean, default=True)
    is_maintenance_mode = db.Column(db.Boolean, default=False)

    @classmethod
    def get_config(cls):
        config = cls.query.first()
        if not config:
            config = cls()
            db.session.add(config)
            db.session.commit()
        return config
