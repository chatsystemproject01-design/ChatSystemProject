from flask import Flask, jsonify, request
from app.config.settings import configs
from app.extensions import init_extensions, socketio
import os

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(configs)
    app.config['SQLALCHEMY_DATABASE_URI'] = configs.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }
    app.config.from_mapping(configs.model_dump())
    
    # Map EMAIL settings to Flask-Mail expected keys
    app.config.update(
        MAIL_SERVER=configs.EMAIL_HOST,
        MAIL_PORT=configs.EMAIL_PORT,
        MAIL_USERNAME=configs.EMAIL_USER,
        MAIL_PASSWORD=configs.EMAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=configs.EMAIL_FROM,
        MAIL_USE_TLS=configs.EMAIL_USE_TLS,
        MAIL_USE_SSL=configs.EMAIL_USE_SSL,
        MAIL_DEBUG=True
    )
    
    # Initialize extensions
    init_extensions(app)
    
    # Configure JWT
    from datetime import timedelta
    app.config['JWT_SECRET_KEY'] = configs.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=configs.JWT_ACCESS_TOKEN_EXPIRES)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(seconds=configs.JWT_REFRESH_TOKEN_EXPIRES)
    
    # Import models (required for migrations)
    from app import models
    
    # Import socket events
    from app.sockets import chat_events, call_events
    
    # Register blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.user_controller import user_bp
    from app.controllers.conversation_controller import conversation_bp
    from app.controllers.media_controller import media_bp
    from app.controllers.ai_controller import ai_bp
    from app.controllers.admin_controller import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(conversation_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)
    
    @app.route('/')
    def health_check():
        return jsonify({"status": "healthy", "message": "Internal Chat System API is running"}), 200
    
    # Centralized error handling
    from app.utils.exceptions import ApplicationError
    from app.models.system_config import SystemConfig

    @app.before_request
    def check_maintenance_mode():
        import sys
        # Logging cưỡng bức ra stdout để Railway bắt được ngay lập tức
        sys.stdout.write(f"\n[DEBUG] Request Started: {request.method} {request.path}\n")
        sys.stdout.flush()
        
        from flask import request, jsonify
        
        # 1. Trả về 200 OK ngay lập tức cho CORS Preflight (OPTIONS) để không lỗi 502
        if request.method == 'OPTIONS':
            return '', 200
            
        # 2. Cho phép các API Auth và Tài liệu API (Swagger) đi qua
        exempt_paths = ['/api/v1/auth', '/api/v1/auth/login/step1', '/apidocs', '/flasgger', '/apispec']
        if any(request.path.startswith(path) for path in exempt_paths):
            return
            
        try:
            # Lấy cache system config (nên dùng cache thay vì query DB liên tục)
            config = SystemConfig.get_config()
            if not config or not config.is_maintenance_mode:
                return
            # ... (phần còn lại của logic admin)
        except Exception:
            pass 
            


    @app.errorhandler(ApplicationError)
    def handle_application_error(error):
        response = {
            "success": False,
            "error_code": error.error_code,
            "message": error.message
        }
        # Thêm request_id vào response (có thể lấy từ g hoặc headers)
        return jsonify(response), error.http_status

    from werkzeug.exceptions import HTTPException
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            "success": False,
            "error_code": f"HTTP_{error.code}",
            "message": error.description
        }), error.code

    @app.after_request
    def add_cors_headers(response):
        # Danh sách các domain được phép
        allowed_origins = [
            "https://fe-chatsystem.onrender.com",
            "http://localhost:5173",
            "http://localhost:3000"
        ]
        
        origin = request.headers.get('Origin')
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, x-requested-with'
        response.headers['Access-Control-Allow-Methods'] = 'GET, PUT, POST, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Đã xảy ra lỗi hệ thống."
        }), 500
    
    return app
