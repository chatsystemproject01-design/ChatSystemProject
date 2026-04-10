from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.ai_service import AIService
from app.utils.exceptions import ValidationError

ai_bp = Blueprint('ai', __name__, url_prefix='/api/v1/ai')
ai_service = AIService()

@ai_bp.route('/summarize', methods=['POST'])
@jwt_required()
def summarize_chat():
    """
    Tóm tắt nội dung cuộc chat bằng AI
    ---
    tags:
      - AI
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - conversationId
          properties:
            conversationId:
              type: integer
            messageLimit:
              type: integer
              default: 100
    responses:
      200:
        description: Tóm tắt thành công
      400:
        description: Lỗi dữ liệu
      403:
        description: Forbidden
    """
    data = request.get_json()
    if not data or 'conversationId' not in data:
        raise ValidationError("Thiếu conversationId.")

    user_id = get_jwt_identity()
    conversation_id = data['conversationId']
    limit = data.get('messageLimit', 100)

    result = ai_service.summarize_conversation(user_id, conversation_id, limit)

    return jsonify({
        "success": True,
        "message": "Tóm tắt thành công.",
        "data": result
    }), 200

@ai_bp.route('/query', methods=['POST'])
@jwt_required()
def ask_ai():
    """
    Đặt câu hỏi cho AI dựa trên dữ liệu nội bộ (RAG)
    ---
    tags:
      - AI
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - question
          properties:
            question:
              type: string
    responses:
      200:
        description: Trả lời thành công
      400:
        description: Câu hỏi không được trống
    """
    data = request.get_json()
    if not data or 'question' not in data:
        raise ValidationError("Thiếu nội dung câu hỏi.")
    
    question = data['question']
    result = ai_service.ask_chatbot(question)

    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200

@ai_bp.route('/detect-toxic', methods=['POST'])
@jwt_required()
def detect_toxic():
    """
    Kiểm tra nội dung tin nhắn nhạy cảm/độc hại
    ---
    tags:
      - AI
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
    responses:
      200:
        description: Kiểm tra hoàn tất
    """
    data = request.get_json()
    if not data or 'text' not in data:
        raise ValidationError("Thiếu nội dung văn bản.")
    
    text = data['text']
    result = ai_service.detect_toxic(text)

    return jsonify({
        "success": True,
        "message": "Kiểm tra hoàn tất.",
        "data": result
    }), 200
