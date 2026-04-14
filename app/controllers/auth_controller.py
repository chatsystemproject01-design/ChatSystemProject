from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError as PydanticValidationError
from app.schemas.auth_schema import (
    RegisterRequestSchema, LoginRequestSchema, Verify2FARequestSchema, 
    ResendOTPRequestSchema, ForgotPasswordRequestSchema, ResetPasswordRequestSchema,
    ChangePasswordRequestSchema
)
from app.services.auth_service import AuthService
from app.utils.exceptions import ValidationError

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Đăng ký tài khoản người dùng mới
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: RegisterRequest
          required:
            - email
            - password
            - fullName
          properties:
            email:
              type: string
              example: "user@example.com"
            password:
              type: string
              example: "Password123!"
            fullName:
              type: string
              example: "Nguyễn Văn A"
            phone:
              type: string
              example: "0912345678"
    responses:
      201:
        description: Đăng ký thành công
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              properties:
                userId:
                  type: integer
      400:
        description: Lỗi validate hoặc Email đã tồn tại
    """
    # Check server config
    from app.models.system_config import SystemConfig
    config = SystemConfig.get_config()
    if not config.is_registration_enabled:
        from app.utils.errors import ForbiddenError
        from flask import abort
        abort(403, "Tính năng đăng ký tài khoản hiện đang bị khóa bởi Quản trị viên.")

    # 1. Parse JSON request
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        # validate data (Rule 2)
        validated_data = RegisterRequestSchema(**json_data)
        
        # 2. Call service layer
        result = auth_service.register_user(validated_data.model_dump())
        
        return jsonify({
            "success": True,
            "message": "Đăng ký thành công. Vui lòng kiểm tra email để nhận mã kích hoạt.",
            "data": result
        }), 201

    except PydanticValidationError as e:
        # Bắn ra lỗi chuẩn hóa để handler xử lý
        raise ValidationError(str(e.errors()))

@auth_bp.route('/login/step1', methods=['POST'])
def login_step1():
    """
    Đăng nhập bước 1: Xác thực Email/Password
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: LoginRequest
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: "user@example.com"
            password:
              type: string
              example: "Password123!"
    responses:
      200:
        description: Xác thực thành công, yêu cầu OTP
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              properties:
                require2FA:
                  type: boolean
      401:
        description: Sai email hoặc mật khẩu
      403:
        description: IP bị khóa do Brute Force
    """
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = LoginRequestSchema(**json_data)
        
        # Lấy IP của người dùng để chống Brute Force
        client_ip = request.remote_addr
        
        result = auth_service.login_step_1(validated_data.model_dump(), client_ip)
        
        return jsonify({
            "success": True,
            "message": "Xác thực bước 1 thành công. Vui lòng nhập mã OTP để đăng nhập.",
            "data": result
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@auth_bp.route('/login/verify-2fa', methods=['POST'])
def verify_2fa():
    """
    Xác thực mã OTP 2FA và cấp JWT Token
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: Verify2FARequest
          required:
            - email
            - otpCode
          properties:
            email:
              type: string
              example: "user@example.com"
            otpCode:
              type: string
              example: "123456"
    responses:
      200:
        description: Xác thực thành công, trả về JWT
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              properties:
                access_token:
                  type: string
                refresh_token:
                  type: string
                user:
                  type: object
      400:
        description: OTP sai hoặc hết hạn
    """
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = Verify2FARequestSchema(**json_data)
        
        result = auth_service.verify_2fa(validated_data.model_dump())
        
        return jsonify({
            "success": True,
            "message": "Xác thực thành công. Chào mừng bạn quay lại.",
            "data": result
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """
    Gửi lại mã OTP
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: ResendOTPRequest
          required:
            - email
          properties:
            email:
              type: string
              example: "user@example.com"
    responses:
      200:
        description: Mã OTP mới đã được gửi
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
      404:
        description: Email không tồn tại
    """
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = ResendOTPRequestSchema(**json_data)
        
        auth_service.resend_otp(validated_data.email)
        
        return jsonify({
            "success": True,
            "message": "Mã OTP mới đã được gửi thành công. Vui lòng kiểm tra email."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Yêu cầu lấy lại mật khẩu
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: ForgotPasswordRequest
          required:
            - email
          properties:
            email:
              type: string
              example: "user@example.com"
    responses:
      200:
        description: Thông báo gửi mã reset thành công (luôn trả về 200 để bảo mật)
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = ForgotPasswordRequestSchema(**json_data)
        
        auth_service.forgot_password(validated_data.email)
        
        return jsonify({
            "success": True,
            "message": "Nếu email tồn tại trong hệ thống, một mã reset mật khẩu đã được gửi đi."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Đặt lại mật khẩu bằng mã OTP
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          id: ResetPasswordRequest
          required:
            - email
            - otpCode
            - newPassword
          properties:
            email:
              type: string
              example: "user@example.com"
            otpCode:
              type: string
              example: "123456"
            newPassword:
              type: string
              example: "NewPassword123!"
    responses:
      200:
        description: Mật khẩu đã được đặt lại thành công
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
      400:
        description: OTP sai hoặc hết hạn
    """
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = ResetPasswordRequestSchema(**json_data)
        
        auth_service.reset_password(validated_data.model_dump())
        
        return jsonify({
            "success": True,
            "message": "Mật khẩu đã được đặt lại thành công. Vui lòng đăng nhập lại bằng mật khẩu mới."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Đổi mật khẩu (Yêu cầu JWT)
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: ChangePasswordRequest
          required:
            - oldPassword
            - newPassword
          properties:
            oldPassword:
              type: string
              example: "OldPassword123!"
            newPassword:
              type: string
              example: "NewPassword123!"
    responses:
      200:
        description: Đổi mật khẩu thành công
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
      401:
        description: Mật khẩu cũ không chính xác hoặc Token hết hạn
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = ChangePasswordRequestSchema(**json_data)
        
        auth_service.change_password(user_id, validated_data.model_dump())
        
        return jsonify({
            "success": True,
            "message": "Mật khẩu đã được đổi thành công."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))
