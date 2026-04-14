import psutil
import os
from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User
from app.models.message import Message
from app.utils.exceptions import ForbiddenError

class AdminService:
    def get_dashboard_stats(self):
        # 1. Đếm số người dùng Online (status active trong 5 phút qua)
        five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
        online_users = User.query.filter(
            User.status == 'active',
            User.last_seen >= five_mins_ago,
            User.is_deleted == False
        ).count()

        # 2. Tổng số tin nhắn
        total_messages = Message.query.count()

        # 3. Thông số hệ thống
        cpu_usage = f"{psutil.cpu_percent()}%"
        
        # RAM usage
        mem = psutil.virtual_memory()
        ram_usage = f"{round(mem.used / (1024**3), 2)}GB/{round(mem.total / (1024**3), 2)}GB"

        return {
            "onlineUsers": online_users,
            "totalMessages": total_messages,
            "system": {
                "cpu": cpu_usage,
                "ram": ram_usage
            }
        }

    def get_pending_users(self, offset=0, limit=20):
        # Truy vấn các user có trạng thái pending
        pending_users = User.query.filter(
            User.status == 'pending',
            User.is_deleted == False
        ).order_by(User.created_at.desc())\
         .offset(offset).limit(limit).all()

        return [
            {
                "userId": str(u.user_id),
                "fullName": u.full_name,
                "email": u.email,
                "phone": u.phone_number,
                "position": u.position,
                "createdAt": u.created_at.isoformat()
            } for u in pending_users
        ]

    def get_all_users(self, offset=0, limit=50):
        # Truy vấn tất cả các user chưa bị xóa
        users = User.query.filter(
            User.is_deleted == False
        ).order_by(User.full_name.asc())\
         .offset(offset).limit(limit).all()

        return [
            {
                "userId": str(u.user_id),
                "fullName": u.full_name,
                "email": u.email,
                "phone": u.phone_number,
                "position": u.position,
                "role": 'admin' if u.role_id == 1 else 'staff',
                "status": u.status,
                "createdAt": u.created_at.isoformat()
            } for u in users
        ]

    def create_user(self, admin_id, data, ip_address):
        from app.extensions import bcrypt
        from app.models.role import Role
        from app.models.audit_log import AdminAuditLog
        from app.repositories import UserRepository
        
        user_repo = UserRepository()
        
        # 1. Kiểm tra tồn tại
        if user_repo.get_by_email(data['email']):
            raise ValidationError("Email đã tồn tại.")

        # 2. Băm mật khẩu
        pw_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')

        try:
            # 3. Tạo User mới (Status active ngay lập tức)
            new_user = User(
                email=data['email'],
                password_hash=pw_hash,
                full_name=data['fullName'],
                role_id=data['roleId'],
                status='active'
            )
            db.session.add(new_user)
            db.session.flush()

            # 4. Ghi Audit Log
            log = AdminAuditLog(
                admin_id=admin_id,
                action_type="CREATE_USER",
                target_id=str(new_user.user_id),
                description=f"Admin created user {new_user.email} with role_id {data['roleId']}",
                ip_address=ip_address
            )
            db.session.add(log)
            db.session.commit()

            return {"userId": str(new_user.user_id)}
        except Exception as e:
            db.session.rollback()
            raise e

    def approve_user(self, admin_id, user_id, ip_address):
        from app.models.audit_log import AdminAuditLog
        from app.repositories import UserRepository
        
        user_repo = UserRepository()
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise ResourceNotFoundError("Người dùng không tồn tại.")
        
        if user.status != 'pending':
            raise ValidationError("Chỉ có thể duyệt các tài khoản đang ở trạng thái Chờ duyệt (Pending).")

        try:
            # 1. Cập nhật trạng thái
            user.status = 'active'
            
            # 2. Ghi Audit Log
            log = AdminAuditLog(
                admin_id=admin_id,
                action_type="APPROVE_USER",
                target_id=str(user.user_id),
                description=f"Admin approved user {user.email}",
                ip_address=ip_address
            )
            db.session.add(log)
            db.session.commit()

            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def update_user(self, admin_id, user_id, data, ip_address):
        from app.models.audit_log import AdminAuditLog
        from app.repositories import UserRepository
        
        user_repo = UserRepository()
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise ResourceNotFoundError("Người dùng không tồn tại.")

        try:
            old_role = user.role_id
            old_position = user.position
            
            # Cập nhật thông tin
            if 'roleId' in data:
                user.role_id = data['roleId']
            if 'position' in data:
                user.position = data['position']
            if 'fullName' in data:
                user.full_name = data['fullName']
            if 'status' in data:
                user.status = data['status']

            # Ghi Audit Log (Chỉ ghi những gì thay đổi chính)
            description = f"Admin updated user {user.email}: "
            if 'roleId' in data: description += f"Role {old_role}->{data['roleId']}. "
            if 'position' in data: description += f"Pos {old_position}->{data['position']}."

            log = AdminAuditLog(
                admin_id=admin_id,
                action_type="UPDATE_USER",
                target_id=str(user.user_id),
                description=description,
                ip_address=ip_address
            )
            db.session.add(log)
            db.session.commit()

            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def delete_user(self, admin_id, user_id, ip_address):
        from app.models.audit_log import AdminAuditLog
        from app.repositories import UserRepository
        
        user_repo = UserRepository()
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise ResourceNotFoundError("Người dùng không tồn tại.")

        try:
            # Xóa mềm
            user.is_deleted = True
            user.status = 'inactive'
            
            # Ghi Audit Log
            log = AdminAuditLog(
                admin_id=admin_id,
                action_type="DELETE_USER",
                target_id=str(user.user_id),
                description=f"Admin soft-deleted user {user.email}",
                ip_address=ip_address
            )
            db.session.add(log)
            db.session.commit()

            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def get_all_reports(self, status=None):
        from app.models.report import Report
        from app.models.user import User
        
        query = db.session.query(Report, User)\
            .join(User, Report.reporter_id == User.user_id)
        
        if status:
            query = query.filter(Report.status == status)
            
        reports = query.order_by(Report.created_at.desc()).all()

        result = []
        for r, u in reports:
            # Lấy thông tin người bị báo cáo nếu có
            reported_user = User.query.get(r.reported_user_id) if r.reported_user_id else None
            
            result.append({
                "reportId": r.report_id,
                "reporter": {
                    "userId": str(u.user_id),
                    "fullName": u.full_name,
                    "email": u.email
                },
                "reportedUser": {
                    "userId": str(reported_user.user_id),
                    "fullName": reported_user.full_name
                } if reported_user else None,
                "reportedMessageId": r.reported_message_id,
                "reasonType": r.reason_type,
                "description": r.description,
                "status": r.status,
                "createdAt": r.created_at.isoformat()
            })
            
        return result

    def handle_report(self, admin_id, report_id, data, ip_address):
        from app.models.report import Report
        from app.models.user import User
        from app.models.audit_log import AdminAuditLog
        
        report = Report.query.get(report_id)
        if not report:
            raise ResourceNotFoundError("Báo cáo không tồn tại.")
        
        action = data.get('action') # block, dismiss, warn
        admin_note = data.get('adminNote')

        try:
            # 1. Thư thi hành động nếu là block
            if action == 'block' and report.reported_user_id:
                reported_user = User.query.get(report.reported_user_id)
                if reported_user:
                    reported_user.status = 'blocked'
            
            # 2. Cập nhật báo cáo
            report.status = 'processed'
            report.processed_by = admin_id
            report.admin_note = admin_note
            
            # 3. Ghi Audit Log
            log = AdminAuditLog(
                admin_id=admin_id,
                action_type=f"HANDLE_REPORT_{action.upper()}",
                target_id=str(report.report_id),
                description=f"Admin handled report {report.report_id} with action {action}. Note: {admin_note}",
                ip_address=ip_address
            )
            db.session.add(log)
            db.session.commit()

            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def get_audit_logs(self, offset=0, limit=20):
        from app.models.audit_log import AdminAuditLog
        from app.models.user import User
        
        query = db.session.query(AdminAuditLog, User)\
            .join(User, AdminAuditLog.admin_id == User.user_id)
        
        logs = query.order_by(AdminAuditLog.created_at.desc())\
            .offset(offset).limit(limit).all()

        return [
            {
                "logId": log.log_id,
                "admin": {
                    "userId": str(u.user_id),
                    "fullName": u.full_name,
                    "email": u.email
                },
                "actionType": log.action_type,
                "targetId": log.target_id,
                "description": log.description,
                "ipAddress": log.ip_address,
                "createdAt": log.created_at.isoformat()
            } for log, u in logs
        ]

    def trigger_db_backup(self, admin_id, ip_address):
        import subprocess
        import os
        from datetime import datetime
        from app.models.audit_log import AdminAuditLog
        from app.config.settings import configs
        
        # 1. Tạo thư mục backups nếu chưa có
        backup_dir = os.path.join(os.getcwd(), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # 2. Định nghĩa tên file: db_backup_YYYYMMDD_HHMMSS.sql
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"db_backup_{timestamp}.sql"
        filepath = os.path.join(backup_dir, filename)
        
        # 3. Thực hiện lệnh pg_dump
        db_url = configs.DATABASE_URL
        
        try:
            # Chạy lệnh pg_dump (yêu cầu pg_dump có sẵn trong PATH server)
            process = subprocess.Popen(
                ['pg_dump', db_url, '-f', filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Lỗi pg_dump: {stderr.decode()}")

            # 4. Ghi Audit Log
            log = AdminAuditLog(
                admin_id=admin_id,
                action_type="DB_BACKUP",
                target_id=filename,
                description=f"Admin triggered manual DB backup. File: {filename}",
                ip_address=ip_address
            )
            db.session.add(log)
            db.session.commit()

            return {"filename": filename, "size": f"{os.path.getsize(filepath) // 1024} KB"}
        except Exception as e:
            db.session.rollback()
            raise e

    def get_conversation_audit(self, admin_id, conversation_id, ip_address):
        from app.models.message import Message
        from app.models.audit_log import AdminAuditLog
        from app.utils.crypto import CryptoUtils
        
        # 1. Ghi log truy cập bí mật (Bắt buộc theo yêu cầu)
        log = AdminAuditLog(
            admin_id=admin_id,
            action_type="AUDIT_CHAT_HISTORY",
            target_id=str(conversation_id),
            description=f"Admin accessed chat history for conversation {conversation_id} for investigation.",
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()

        # 2. Lấy tin nhắn
        messages = Message.query.filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at.asc()).all()
            
        return [
            {
                "messageId": str(m.message_id),
                "senderId": str(m.sender_id),
                "senderName": m.sender.full_name if m.sender else "Unknown",
                "content": CryptoUtils.decrypt(m.message_content) if m.message_type == 'text' else "[File/Image Attachment]",
                "type": m.message_type,
                "isToxic": m.is_toxic,
                "createdAt": m.created_at.isoformat()
            } for m in messages
        ]

    def get_all_conversations(self, offset=0, limit=50):
        from app.models.conversation import Conversation
        
        convs = Conversation.query.filter(Conversation.is_deleted == False)\
            .order_by(Conversation.created_at.desc())\
            .offset(offset).limit(limit).all()
            
        return [
            {
                "conversationId": c.conversation_id,
                "conversationName": c.conversation_name or "Chat cá nhân",
                "isGroup": c.is_group,
                "updatedAt": c.created_at.isoformat()
            } for c in convs
        ]

    def update_registration_config(self, admin_id, is_enabled, ip_address):
        from app.models.system_config import SystemConfig
        from app.models.audit_log import AdminAuditLog
        
        config = SystemConfig.get_config()
        config.is_registration_enabled = is_enabled
        
        log = AdminAuditLog(
            admin_id=admin_id,
            action_type="UPDATE_CONFIG_REGISTRATION",
            target_id="system",
            description=f"Admin turned {'ON' if is_enabled else 'OFF'} public registration.",
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        return {"isEnabled": config.is_registration_enabled}

    def update_maintenance_config(self, admin_id, is_maintenance, ip_address):
        from app.models.system_config import SystemConfig
        from app.models.audit_log import AdminAuditLog
        
        config = SystemConfig.get_config()
        config.is_maintenance_mode = is_maintenance
        
        log = AdminAuditLog(
            admin_id=admin_id,
            action_type="UPDATE_CONFIG_MAINTENANCE",
            target_id="system",
            description=f"Admin turned {'ON' if is_maintenance else 'OFF'} maintenance mode.",
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        return {"isMaintenance": config.is_maintenance_mode}

    def check_system_health(self):
        status = {
            "database": "disconnected",
            "socket": "stable",
            "firebase": "disconnected"
        }
        try:
            db.session.execute(db.text('SELECT 1'))
            status["database"] = "connected"
        except:
            pass
            
        try:
            import firebase_admin
            if firebase_admin._apps:
                status["firebase"] = "connected"
        except:
            pass
            
        return status
