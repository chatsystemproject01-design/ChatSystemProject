from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError as PydanticValidationError
from app.schemas.user_schema import AddContactRequestSchema, UpdateProfileRequestSchema, BlockUserRequestSchema
from app.services.user_service import UserService
from app.utils.exceptions import ValidationError

user_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')
user_service = UserService()

@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """
    Lấy thông tin người dùng hiện tại
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Lấy thông tin thành công
        schema:
          properties:
            success:
              type: boolean
            data:
              type: object
      401:
        description: Token không hợp lệ
    """
    user_id = get_jwt_identity()
    result = user_service.get_my_profile(user_id)
    
    return jsonify({
        "success": True,
        "message": "Lấy thông tin thành công.",
        "data": result
    }), 200

@user_bp.route('/contacts', methods=['GET'])
@jwt_required()
def get_contacts():
    """
    Xem danh sách đồng nghiệp và trạng thái trực tuyến
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Lấy danh sách thành công
        schema:
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                properties:
                  userId:
                    type: string
                  fullName:
                    type: string
                  status:
                    type: string
                  lastSeen:
                    type: string
    """
    user_id = get_jwt_identity()
    result = user_service.get_contacts(user_id)
    
    return jsonify({
        "success": True,
        "message": "Lấy danh sách đồng nghiệp thành công.",
        "data": result
    }), 200

@user_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    """
    Tìm kiếm người dùng hệ thống
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: query
        name: q
        type: string
        required: true
        description: Email hoặc Tên người dùng (tối thiểu 2 ký tự)
    responses:
      200:
        description: Tìm kiếm thành công
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: array
    """
    query = request.args.get('q', '')
    if len(query) < 2:
        from app.utils.exceptions import ValidationError
        raise ValidationError("Từ khóa tìm kiếm phải có tối thiểu 2 ký tự.")

    current_user_id = get_jwt_identity()
    result = user_service.search_users(query, current_user_id)
    
    return jsonify({
        "success": True,
        "message": f"Tìm thấy {len(result)} kết quả.",
        "data": result
    }), 200

@user_bp.route('/contacts', methods=['POST'])
@jwt_required()
def add_contact():
    """
    Thêm người dùng vào danh sách liên hệ
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: AddContactRequest
          required:
            - colleagueId
          properties:
            colleagueId:
              type: string
              example: "UUID-of-colleague"
    responses:
      201:
        description: Đã thêm vào danh sách liên hệ
      400:
        description: Dữ liệu không hợp lệ hoặc đã tồn tại
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = AddContactRequestSchema(**json_data)
        
        user_service.add_contact(user_id, validated_data.colleagueId)
        
        return jsonify({
            "success": True,
            "message": "Đã thêm vào danh sách liên hệ thành công."
        }), 201

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@user_bp.route('/contacts/<string:id>', methods=['DELETE'])
@jwt_required()
def remove_contact(id):
    """
    Xóa liên hệ khỏi danh sách
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: string
        required: true
        description: UUID của đồng nghiệp cần xóa
    responses:
      200:
        description: Đã xóa khỏi danh sách liên hệ
      404:
        description: Liên hệ không tồn tại
    """
    user_id = get_jwt_identity()
    user_service.remove_contact(user_id, id)
    
    return jsonify({
        "success": True,
        "message": "Đã xóa khỏi danh sách liên hệ thành công."
    }), 200

@user_bp.route('/block', methods=['POST'])
@jwt_required()
def block_user():
    """
    Chặn người dùng khác
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: BlockUserRequest
          required:
            - targetUserId
          properties:
            targetUserId:
              type: string
              example: "UUID-of-user-to-block"
    responses:
      200:
        description: Đã chặn người dùng thành công
      400:
        description: Dữ liệu không hợp lệ hoặc chặn chính mình
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = BlockUserRequestSchema(**json_data)
        
        user_service.block_user(user_id, validated_data.targetUserId)
        
        return jsonify({
            "success": True,
            "message": "Đã chặn người dùng thành công."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@user_bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    """
    Cập nhật thông tin cá nhân
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: UpdateProfileRequest
          properties:
            fullName:
              type: string
            phoneNumber:
              type: string
            dateOfBirth:
              type: string
              example: "1990-01-01"
            position:
              type: string
            avatarUrl:
              type: string
    responses:
      200:
        description: Đã cập nhật thông tin cá nhân
        schema:
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = UpdateProfileRequestSchema(**json_data)
        
        user_service.update_profile(user_id, validated_data.model_dump())
        
        return jsonify({
            "success": True,
            "message": "Cập nhật thông tin cá nhân thành công."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@user_bp.route('/report', methods=['POST'])
@jwt_required()
def create_report():
    """
    Người dùng báo cáo vi phạm (Spam/Toxic)
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - reasonType
          properties:
            reportedUserId:
              type: string
            reportedMessageId:
              type: integer
            reasonType:
              type: string
            description:
              type: string
    responses:
      201:
        description: Cảm ơn bạn đã báo cáo
    """
    reporter_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    report_id = user_service.create_report(reporter_id, data)
    
    return jsonify({
        "success": True,
        "message": "Cảm ơn bạn đã báo cáo. Chúng tôi sẽ xử lý sớm.",
        "reportId": report_id
    }), 201

@user_bp.route('/reports/me', methods=['GET'])
@jwt_required()
def get_my_reports():
    """
    Xem lịch sử các báo cáo đã gửi
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Lấy danh sách thành công
        schema:
          properties:
            success:
              type: boolean
            data:
              type: array
    """
    user_id = get_jwt_identity()
    result = user_service.get_my_reports(user_id)
    
    return jsonify({
        "success": True,
        "message": "Lấy lịch sử báo cáo thành công.",
        "data": result
    }), 200

@user_bp.route('/report/reasons', methods=['GET'])
@jwt_required()
def get_report_reasons():
    """
    Lấy danh sách các lý do báo cáo mẫu
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Lấy danh sách thành công
    """
    result = user_service.get_report_reasons()
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200
