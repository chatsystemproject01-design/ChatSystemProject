from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError as PydanticValidationError
from app.schemas.conversation_schema import CreateConversationRequestSchema, UpdateConversationRequestSchema, AddMemberRequestSchema, RemoveMemberRequestSchema, LeaveGroupRequestSchema, TransferOwnerRequestSchema, SendMessageRequestSchema, EditMessageRequestSchema
from app.services.conversation_service import ConversationService
from app.utils.exceptions import ValidationError

conversation_bp = Blueprint('conversations', __name__, url_prefix='/api/v1/conversations')
conversation_service = ConversationService()

@conversation_bp.route('/transfer-owner', methods=['PATCH'])
@jwt_required()
def transfer_owner():
    """
    Chuyển quyền trưởng nhóm
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: TransferOwnerRequest
          properties:
            conversationId:
              type: integer
            newOwnerId:
              type: string
    responses:
      200:
        description: Đã chuyển quyền trưởng nhóm thành công
    """
    current_owner_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = TransferOwnerRequestSchema(**json_data)
        conversation_service.transfer_owner(
            current_owner_id, 
            validated_data.conversationId, 
            validated_data.newOwnerId
        )
        
        return jsonify({
            "success": True,
            "message": "Đã chuyển quyền trưởng nhóm thành công."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))


@conversation_bp.route('/members', methods=['DELETE'])
@jwt_required()
def remove_member():
    """
    Xóa thành viên khỏi nhóm
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: RemoveMemberRequest
          properties:
            conversationId:
              type: integer
            memberIdToRemove:
              type: string
    responses:
      200:
        description: Thành viên đã bị xóa khỏi nhóm
    """
    admin_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = RemoveMemberRequestSchema(**json_data)
        conversation_service.remove_member(
            admin_id, 
            validated_data.conversationId, 
            validated_data.memberIdToRemove
        )
        
        return jsonify({
            "success": True,
            "message": "Thành viên đã bị xóa khỏi nhóm."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@conversation_bp.route('/leave', methods=['POST'])
@jwt_required()
def leave_group():
    """
    Tự rời khỏi nhóm chat
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: LeaveGroupRequest
          properties:
            conversationId:
              type: integer
    responses:
      200:
        description: Bạn đã rời khỏi nhóm
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = LeaveGroupRequestSchema(**json_data)
        conversation_service.leave_group(user_id, validated_data.conversationId)
        
        return jsonify({
            "success": True,
            "message": "Bạn đã rời khỏi nhóm."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))


@conversation_bp.route('/<int:id>/members', methods=['GET'])
@jwt_required()
def get_conversation_members(id):
    """
    Xem danh sách thành viên trong nhóm
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Thành công
    """
    user_id = get_jwt_identity()
    result = conversation_service.get_conversation_members(user_id, id)
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200

@conversation_bp.route('/members', methods=['POST'])
@jwt_required()
def add_member():
    """
    Thêm thành viên vào nhóm
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: AddMemberRequest
          properties:
            conversationId:
              type: integer
            newMemberId:
              type: string
    responses:
      201:
        description: Đã thêm thành viên vào nhóm
      400:
        description: Bad Request
    """
    admin_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = AddMemberRequestSchema(**json_data)
        conversation_service.add_member(
            admin_id, 
            validated_data.conversationId, 
            validated_data.newMemberId
        )
        
        return jsonify({
            "success": True,
            "message": "Đã thêm thành viên vào nhóm."
        }), 201

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))



@conversation_bp.route('', methods=['POST'])
@jwt_required()
def create_conversation():
    """
    Tạo phòng chat mới (Cá nhân hoặc Nhóm)
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: CreateConversationRequest
          properties:
            isGroup:
              type: boolean
              example: false
            conversationName:
              type: string
              example: "Team A"
            targetUserId:
              type: string
              example: "UUID-of-target"
            memberIds:
              type: array
              items:
                type: string
    responses:
      201:
        description: Tạo cuộc hội thoại thành công
        schema:
          properties:
            success:
              type: boolean
            data:
              properties:
                conversationId:
                  type: integer
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = CreateConversationRequestSchema(**json_data)
        result = conversation_service.create_conversation(user_id, validated_data.model_dump())
        
        return jsonify({
            "success": True,
            "message": "Tạo cuộc hội thoại thành công.",
            "data": result
        }), 201

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@conversation_bp.route('', methods=['GET'])
@jwt_required()
def get_conversations():
    """
    Lấy danh sách hội thoại của người dùng
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    responses:
      200:
        description: Thành công
        schema:
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                properties:
                  conversationId:
                    type: integer
                  name:
                    type: string
                  lastMessage:
                    type: string
                  unreadCount:
                    type: integer
    """
    user_id = get_jwt_identity()
    result = conversation_service.get_user_conversations(user_id)
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200

@conversation_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_conversation(id):
    """
    Cập nhật thông tin phòng chat
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          id: UpdateConversationRequest
          properties:
            conversationName:
              type: string
            avatarUrl:
              type: string
    responses:
      200:
        description: Cập nhật thành công
      403:
        description: Forbidden
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = UpdateConversationRequestSchema(**json_data)
        conversation_service.update_conversation(user_id, id, validated_data.model_dump())
        
        return jsonify({
            "success": True,
            "message": "Cập nhật thành công."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@conversation_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_conversation_detail(id):
    """
    Lấy thông tin chi tiết phòng chat
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Thành công
      403:
        description: Forbidden
    """
    user_id = get_jwt_identity()
    result = conversation_service.get_conversation_detail(user_id, id)
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200

@conversation_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(id):
    """
    Xóa mềm hội thoại
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Đã xóa hội thoại
      403:
        description: Forbidden
    """
    user_id = get_jwt_identity()
    conversation_service.delete_conversation(user_id, id)
    
    return jsonify({
        "success": True,
        "message": "Đã xóa hội thoại."
    }), 200
    
@conversation_bp.route('/<int:id>/messages', methods=['GET'])
@jwt_required()
def get_chat_history(id):
    """
    Lấy danh sách tin nhắn trong một cuộc hội thoại (Giải mã AES)
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: query
        name: offset
        type: integer
        default: 0
      - in: query
        name: limit
        type: integer
        default: 50
    responses:
      200:
        description: Thành công
        schema:
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                properties:
                  messageId:
                    type: integer
                  content:
                    type: string
                  senderId:
                    type: string
                  createdAt:
                    type: string
    """
    user_id = get_jwt_identity()
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    result = conversation_service.get_chat_history(user_id, id, offset, limit)
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200

@conversation_bp.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    """
    Gửi tin nhắn (Cơ chế dự phòng cho Socket - Mã hóa AES & DLP)
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          id: SendMessageRequest
          required:
            - conversationId
            - messageContent
          properties:
            conversationId:
              type: integer
            messageContent:
              type: string
            messageType:
              type: string
              default: "text"
    responses:
      201:
        description: Tin nhắn đã gửi
        schema:
          properties:
            success:
              type: boolean
            data:
              properties:
                messageId:
                  type: integer
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = SendMessageRequestSchema(**json_data)
        result = conversation_service.send_message(user_id, validated_data.model_dump())
        
        return jsonify({
            "success": True,
            "message": "Tin nhắn đã gửi.",
            "data": result
        }), 201

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@conversation_bp.route('/messages/<int:id>', methods=['PUT'])
@jwt_required()
def edit_message(id):
    """
    Chỉnh sửa tin nhắn đã gửi (Giới hạn 15 phút)
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          id: EditMessageRequest
          required:
            - newContent
          properties:
            newContent:
              type: string
    responses:
      200:
        description: Tin nhắn đã được cập nhật
      403:
        description: Forbidden
      400:
        description: Quá thời gian chỉnh sửa
    """
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        raise ValidationError("Không tìm thấy dữ liệu request.")

    try:
        validated_data = EditMessageRequestSchema(**json_data)
        conversation_service.edit_message(user_id, id, validated_data.newContent)
        
        return jsonify({
            "success": True,
            "message": "Tin nhắn đã được cập nhật."
        }), 200

    except PydanticValidationError as e:
        raise ValidationError(str(e.errors()))

@conversation_bp.route('/messages/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_message(id):
    """
    Xóa mềm tin nhắn
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Tin nhắn đã bị xóa
      403:
        description: Forbidden
    """
    user_id = get_jwt_identity()
    conversation_service.delete_message(user_id, id)
    
    return jsonify({
        "success": True,
        "message": "Tin nhắn đã bị xóa."
    }), 200

@conversation_bp.route('/messages/<int:id>/pin', methods=['POST'])
@jwt_required()
def pin_message(id):
    """
    Ghim tin nhắn lên đầu hội thoại
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Đã ghim tin nhắn
      403:
        description: Forbidden
    """
    user_id = get_jwt_identity()
    conversation_service.pin_message(user_id, id, is_pinned=True)
    
    return jsonify({
        "success": True,
        "message": "Đã ghim tin nhắn."
    }), 200

@conversation_bp.route('/messages/<int:id>/unpin', methods=['POST'])
@jwt_required()
def unpin_message(id):
    """
    Bỏ ghim tin nhắn
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Đã bỏ ghim
    """
    user_id = get_jwt_identity()
    conversation_service.pin_message(user_id, id, is_pinned=False)
    
    return jsonify({
        "success": True,
        "message": "Đã bỏ ghim tin nhắn."
    }), 200

@conversation_bp.route('/messages/forward', methods=['POST'])
@jwt_required()
def forward_message():
    """
    Chuyển tiếp tin nhắn sang phòng chat khác
    ---
    tags:
      - Conversations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - sourceMessageId
            - targetConversationIds
          properties:
            sourceMessageId:
              type: integer
            targetConversationIds:
              type: array
              items:
                type: integer
    responses:
      201:
        description: Đã chuyển tiếp tin nhắn
    """
    data = request.get_json()
    user_id = get_jwt_identity()
    conversation_service.forward_message(user_id, data)
    
    return jsonify({
        "success": True,
        "message": "Đã chuyển tiếp tin nhắn."
    }), 201

