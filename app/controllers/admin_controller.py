from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.services.admin_service import AdminService
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')
admin_service = AdminService()

@admin_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@admin_required()
def get_dashboard_stats():
    """
    Xem thông số thống kê Dashboard (Yêu cầu Admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: Lấy thống kê thành công
      403:
        description: Không có quyền admin
    """
    result = admin_service.get_dashboard_stats()
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200

@admin_bp.route('/users/pending', methods=['GET'])
@jwt_required()
@admin_required()
def get_pending_users():
    """
    Danh sách tài khoản chờ duyệt đăng ký (Yêu cầu Admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - name: offset
        in: query
        type: integer
        default: 0
      - name: limit
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: Lấy danh sách thành công
    """
    from flask import request
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    result = admin_service.get_pending_users(offset, limit)
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@admin_required()
def create_user():
    """
    Admin cấp tài khoản trực tiếp cho nhân viên
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - email
            - password
            - fullName
            - roleId
          properties:
            email:
              type: string
            password:
              type: string
            fullName:
              type: string
            roleId:
              type: integer
    responses:
      201:
        description: Tài khoản nhân viên đã được tạo
    """
    from flask import request
    from flask_jwt_extended import get_jwt_identity
    
    admin_id = get_jwt_identity()
    data = request.get_json()
    ip_address = request.remote_addr
    
    result = admin_service.create_user(admin_id, data, ip_address)
    
    return jsonify({
        "success": True,
        "message": "Tài khoản nhân viên đã được tạo.",
        "data": result
    }), 201

@admin_bp.route('/users/<string:id>/approve', methods=['PATCH'])
@jwt_required()
@admin_required()
def approve_user(id):
    """
    Duyệt tài khoản nhân viên mới (Yêu cầu Admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Tài khoản đã được duyệt
    """
    from flask import request
    from flask_jwt_extended import get_jwt_identity
    
    admin_id = get_jwt_identity()
    ip_address = request.remote_addr
    
    admin_service.approve_user(admin_id, id, ip_address)
    
    return jsonify({
        "success": True,
        "message": "Tài khoản đã được duyệt thành công."
    }), 200

@admin_bp.route('/users/<string:id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_user(id):
    """
    Cập nhật quyền (Role) hoặc thông tin Staff (Yêu cầu Admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            roleId:
              type: integer
            position:
              type: string
            fullName:
              type: string
            status:
              type: string
    responses:
      200:
        description: Thông tin nhân viên đã được cập nhật
    """
    from flask import request
    from flask_jwt_extended import get_jwt_identity
    
    admin_id = get_jwt_identity()
    data = request.get_json()
    ip_address = request.remote_addr
    
    admin_service.update_user(admin_id, id, data, ip_address)
    
    return jsonify({
        "success": True,
        "message": "Thông tin nhân viên đã được cập nhật thành công."
    }), 200

@admin_bp.route('/users/<string:id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user(id):
    """
    Xóa mềm tài khoản nhân viên (Yêu cầu Admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Tài khoản đã bị xóa khỏi hệ thống
    """
    from flask import request
    from flask_jwt_extended import get_jwt_identity
    
    admin_id = get_jwt_identity()
    ip_address = request.remote_addr
    
    admin_service.delete_user(admin_id, id, ip_address)
    
    return jsonify({
        "success": True,
        "message": "Tài khoản đã bị xóa khỏi hệ thống thành công."
    }), 200

@admin_bp.route('/reports', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_reports():
    """
    Danh sách các báo cáo vi phạm toàn hệ thống (Yêu cầu Admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - name: status
        in: query
        type: string
        description: Lọc theo trạng thái (pending/processed)
    responses:
      200:
        description: Lấy danh sách thành công
    """
    from flask import request
    status = request.args.get('status')
    
    result = admin_service.get_all_reports(status)
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200

@admin_bp.route('/reports/<int:id>/action', methods=['PATCH'])
@jwt_required()
@admin_required()
def handle_report(id):
    """
    Xử lý báo cáo vi phạm (Yêu cầu Admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          required:
            - action
          properties:
            action:
              type: string
              enum: [block, warn, dismiss]
            adminNote:
              type: string
    responses:
      200:
        description: Đã xử lý báo cáo thành công
    """
    from flask import request
    from flask_jwt_extended import get_jwt_identity
    
    admin_id = get_jwt_identity()
    data = request.get_json()
    ip_address = request.remote_addr
    
    admin_service.handle_report(admin_id, id, data, ip_address)
    
    return jsonify({
        "success": True,
        "message": "Đã xử lý báo cáo thành công."
    }), 200

@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@admin_required()
def get_audit_logs():
    """
    Xem lịch sử hành động của Ban quản trị (Yêu cầu Admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - name: offset
        in: query
        type: integer
        default: 0
      - name: limit
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: Lấy danh sách thành công
    """
    from flask import request
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    result = admin_service.get_audit_logs(offset, limit)
    
    return jsonify({
        "success": True,
        "message": "Thành công.",
        "data": result
    }), 200

@admin_bp.route('/db/backup', methods=['POST'])
@jwt_required()
@admin_required()
def trigger_db_backup():
    """
    Kích hoạt luồng sao lưu CSDL (Yêu cầu Admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      202:
        description: Tiến trình sao lưu đã được bắt đầu
    """
    from flask import request
    from flask_jwt_extended import get_jwt_identity
    
    admin_id = get_jwt_identity()
    ip_address = request.remote_addr
    
    result = admin_service.trigger_db_backup(admin_id, ip_address)
    
    return jsonify({
        "success": True,
        "message": "Tiến trình sao lưu đã được thực hiện thành công.",
        "data": result
    }), 202
