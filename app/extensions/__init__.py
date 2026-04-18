from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flasgger import Swagger

db = SQLAlchemy()
bcrypt = Bcrypt()
socketio = SocketIO()
migrate = Migrate()
cors = CORS()
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Internal Chat System API",
        "version": "1.0.0",
        "description": "Hệ thống API cho ứng dụng chat nội bộ công ty."
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": 'JWT Authorization header. Nhập theo mẫu: "Bearer {token}"'
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ]
}

swagger = Swagger(template=swagger_template)
mail = Mail()
jwt = JWTManager()

def init_extensions(app):
    db.init_app(app)
    bcrypt.init_app(app)
    # Cấu hình danh sách các Domain được phép truy cập (Whitelist)
    allowed_origins = [
        "https://fe-chatsystem.onrender.com",
        "http://localhost:5173",
        "http://localhost:3000"
    ]
    
    # Cài đặt Socket.IO - Đọc từ biến môi trường (Local: threading, Production: gevent)
    async_mode = app.config.get('SOCKETIO_ASYNC_MODE', 'threading')
    socketio.init_app(app, cors_allowed_origins=allowed_origins, async_mode=async_mode)
    
    migrate.init_app(app, db)
    cors.init_app(app) # Trả về khởi tạo cơ bản
    mail.init_app(app)
    jwt.init_app(app)
    swagger.init_app(app)
