from flask import Flask, jsonify
from app.config.settings import configs
from app.extensions import init_extensions, socketio
import os

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(configs)
    app.config['SQLALCHEMY_DATABASE_URI'] = configs.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.from_mapping(configs.model_dump())
    
    # Map EMAIL settings to Flask-Mail expected keys
    app.config.update(
        MAIL_SERVER=configs.EMAIL_HOST,
        MAIL_PORT=configs.EMAIL_PORT,
        MAIL_USERNAME=configs.EMAIL_USER,
        MAIL_PASSWORD=configs.EMAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=configs.EMAIL_FROM,
        MAIL_USE_TLS=configs.EMAIL_USE_TLS,
        MAIL_USE_SSL=configs.EMAIL_USE_SSL
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
    
    # Centralized error handling
    from app.utils.exceptions import ApplicationError

    @app.before_request
    def check_maintenance_mode():
        from flask import request, jsonify
        
        # 1. Cho phép CORS Preflight (OPTIONS) đi qua để không lỗi Frontend
        if request.method == 'OPTIONS':
            return
            
        # 2. Cho phép các API Auth không xác thực đi qua
        if request.path.startswith('/api/v1/auth'):
            return
            
        try:
            from app.models.system_config import SystemConfig
            config = SystemConfig.get_config()
            if not config.is_maintenance_mode:
                return
                
            # 3. Cho phép Admin truy cập mọi lúc
            from flask_jwt_extended import verify_jwt_in_request, get_jwt
            try:
                verify_jwt_in_request(optional=True)
                claims = get_jwt()
                if claims.get('role', '').lower() == 'admin':
                    return
            except Exception:
                pass 

            return jsonify({
                "success": False,
                "message": "Hệ thống đang được bảo trì. Vui lòng quay lại sau."
            }), 503
        except Exception as e:
            app.logger.error(f"Error in maintenance check: {str(e)}")
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

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        import traceback
        traceback.print_exc()
        # Log error in production
        return jsonify({
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Đã xảy ra lỗi hệ thống."
        }), 500
    
    return app
