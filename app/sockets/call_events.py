from app.extensions import socketio, db
from flask_socketio import emit
from flask import request
from app.sockets.chat_events import connected_users, _get_current_user_id
from app.models.call_log import CallLog
from app.repositories import UserRepository
import datetime

user_repo = UserRepository()

def _get_sids_for_user(user_id):
    """Lấy danh sách socket ID của một user_id cụ thể (trường hợp đăng nhập nhiều nơi)"""
    return [sid for sid, uid in connected_users.items() if str(uid) == str(user_id)]

@socketio.on('call_user')
def handle_call_user(data):
    """
    Client khởi tạo cuộc gọi.
    Payload: { receiverId: 'uuid', callType: 'voice/video', signalData: {...} }
    """
    caller_id = _get_current_user_id()
    if not caller_id:
        return
        
    receiver_id = data.get('receiverId')
    call_type = data.get('callType', 'voice')
    
    if not receiver_id:
        emit('call_error', {'message': 'receiverId is required'})
        return
        
    caller = user_repo.get_by_id(caller_id)
    
    from app.models.participant import ConversationParticipant
    from app.models.contact import Contact
    
    # Kiểm tra bảo mật: Phải là bạn bè hoặc từng chat chung
    is_contact = Contact.query.filter_by(user_id=caller_id, contact_user_id=receiver_id, status='accepted').first()
    if not is_contact:
        is_contact_reverse = Contact.query.filter_by(user_id=receiver_id, contact_user_id=caller_id, status='accepted').first()
        if not is_contact_reverse:
            subq = db.session.query(ConversationParticipant.conversation_id).filter_by(user_id=caller_id).subquery()
            shared_conv = db.session.query(ConversationParticipant).filter(
                ConversationParticipant.user_id == receiver_id,
                ConversationParticipant.conversation_id.in_(subq)
            ).first()
            if not shared_conv:
                emit('call_error', {'message': 'Chỉ cho phép gọi người đã có liên hệ hoặc nhắn tin chung.'})
                return
    
    # Kiểm tra trạng thái online của receiver
    receiver_sids = _get_sids_for_user(receiver_id)
    if not receiver_sids:
        # Lưu cuộc gọi nhỡ ngay
        call = CallLog(
            caller_id=caller_id,
            receiver_id=receiver_id,
            call_type=call_type,
            status='missed',
            end_time=datetime.datetime.utcnow()
        )
        db.session.add(call)
        db.session.commit()
        emit('call_error', {'message': 'Người dùng hiện không online.'})
        return
        
    # Tạo bản ghi log cuộc gọi
    call = CallLog(
        caller_id=caller_id,
        receiver_id=receiver_id,
        call_type=call_type,
        status='initiated'
    )
    db.session.add(call)
    db.session.commit()
    
    # Gửi thông báo đến người nhận (Signaling: SDP Offer)
    for sid in receiver_sids:
        emit('incoming_call', {
            'callId': str(call.call_id),
            'callerId': str(caller_id),
            'callerName': caller.full_name,
            'callerAvatar': caller.avatar_url,
            'callType': call_type,
            'signalData': data.get('signalData')
        }, room=sid)


@socketio.on('call_accepted')
def handle_call_accepted(data):
    """
    Người nhận đồng ý tham gia cuộc gọi.
    Payload: { callId, signalData: {...} }
    """
    receiver_id = _get_current_user_id()
    if not receiver_id:
        return
        
    call_id = data.get('callId')
    call = db.session.get(CallLog, call_id)
    
    if not call or str(call.receiver_id) != str(receiver_id):
        return
        
    call.status = 'ongoing'
    db.session.commit()
    
    # Gửi SDP Answer lại cho người gọi
    caller_sids = _get_sids_for_user(call.caller_id)
    for sid in caller_sids:
        emit('call_accepted', {
            'callId': call_id,
            'signalData': data.get('signalData')
        }, room=sid)


@socketio.on('call_rejected')
def handle_call_rejected(data):
    """
    Người nhận từ chối cuộc gọi.
    Payload: { callId }
    """
    receiver_id = _get_current_user_id()
    if not receiver_id:
        return
        
    call_id = data.get('callId')
    call = db.session.get(CallLog, call_id)
    
    if not call or str(call.receiver_id) != str(receiver_id):
        return
        
    call.status = 'rejected'
    call.end_time = datetime.datetime.utcnow()
    db.session.commit()
    
    # Báo người gọi biết bị từ chối
    caller_sids = _get_sids_for_user(call.caller_id)
    for sid in caller_sids:
        emit('call_rejected', {'callId': call_id}, room=sid)


@socketio.on('webrtc_signal')
def handle_webrtc_signal(data):
    """
    Chuyển tiếp (Relay) thông tin ICE Candidate hoặc SDP Re-negotiation.
    Payload: { targetId: 'uuid', signalData: {...} }
    """
    sender_id = _get_current_user_id()
    if not sender_id:
        return
        
    target_id = data.get('targetId')
    target_sids = _get_sids_for_user(target_id)
    
    for sid in target_sids:
        emit('webrtc_signal', {
            'senderId': sender_id,
            'signalData': data.get('signalData')
        }, room=sid)


@socketio.on('end_call')
def handle_end_call(data):
    """
    Tắt máy/Kết thúc cuộc gọi hiện tại.
    Payload: { callId }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return
        
    call_id = data.get('callId')
    call = db.session.get(CallLog, call_id)
    if not call:
        return
        
    # Kiểm tra tính hợp lệ
    orig_caller = str(call.caller_id)
    orig_receiver = str(call.receiver_id)
    if orig_caller != str(user_id) and orig_receiver != str(user_id):
        return
        
    call.status = 'completed'
    call.end_time = datetime.datetime.utcnow()
    # Tính thời lượng thực tế
    timediff = call.end_time - call.start_time
    call.duration = int(timediff.total_seconds())
    db.session.commit()
    
    # Thông báo cho bên kia biết để đóng UI/MediaStream
    other_id = orig_receiver if orig_caller == str(user_id) else orig_caller
    other_sids = _get_sids_for_user(other_id)
    for sid in other_sids:
        emit('end_call', {'callId': call_id}, room=sid)
