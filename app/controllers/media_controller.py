from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.media_service import MediaService
from app.utils.exceptions import ValidationError

media_bp = Blueprint('media', __name__, url_prefix='/api/v1/media')
media_service = MediaService()

@media_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_media():
    """
    Upload ảnh/file lên Supabase Storage (Kiểm tra Magic Bytes)
    Nếu truyền conversationId, tệp tin sẽ tự động được gửi vào tin nhắn.
    ---
    tags:
      - Media
    security:
      - Bearer: []
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Tệp tin cần upload (Max 20MB, chặn .exe, .js, .bat)
      - in: formData
        name: conversationId
        type: integer
        required: false
        description: ID của cuộc hội thoại để gửi tệp tin vào tin nhắn
    responses:
      201:
        description: Tải lên thành công
      415:
        description: Định dạng file không được hỗ trợ
      400:
        description: Lỗi dữ liệu hoặc kích thước quá lớn
    """
    if 'file' not in request.files:
        raise ValidationError("Không tìm thấy tệp tin trong request.")
    
    file = request.files['file']
    if file.filename == '':
        raise ValidationError("Tên tệp tin không hợp lệ.")

    conversation_id = request.form.get('conversationId')
    if conversation_id:
        conversation_id = int(conversation_id)
        
    message_type = request.form.get('messageType', 'media')
    duration = request.form.get('duration')
    
    if duration is not None:
        try:
            duration = int(duration)
            if duration > 600: # Max 10 minutes
                raise ValidationError("Thời lượng tin nhắn thoại không vượt quá 10 phút.")
        except ValueError:
            raise ValidationError("Thời lượng phải là một số nguyên (giây).")

    user_id = get_jwt_identity()
    result = media_service.upload_media(user_id, file, conversation_id, message_type, duration)
    
    return jsonify({
        "success": True,
        "message": "Tải lên thành công.",
        "data": result
    }), 201

@media_bp.route('/conversation/<int:cid>', methods=['GET'])
@jwt_required()
def get_conversation_media(cid):
    """
    Lấy toàn bộ ảnh/file đã chia sẻ trong phòng chat
    ---
    tags:
      - Media
    security:
      - Bearer: []
    parameters:
      - in: path
        name: cid
        type: integer
        required: true
        description: ID của cuộc hội thoại
    responses:
      200:
        description: Danh sách tệp tin
      403:
        description: Không có quyền truy cập
    """
    user_id = get_jwt_identity()
    result = media_service.get_conversation_media(user_id, cid)
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200
