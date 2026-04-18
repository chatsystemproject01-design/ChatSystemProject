import threading
from app.extensions import socketio, db
from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
from flask_jwt_extended import decode_token
from app.repositories import UserRepository, ParticipantRepository

# ════════════════════════════════════════════════
# IN-MEMORY STATE
# ════════════════════════════════════════════════
connected_users = {}   # { sid: user_id }
user_rooms = {}        # { sid: set(room_names) }
typing_timers = {}     # { "userId_convId": threading.Timer }

TYPING_TIMEOUT = 5.0   # Giây

user_repo = UserRepository()
participant_repo = ParticipantRepository()


def emit_to_user(target_user_id, event_name, data=None):
    """Gửi socket event tới tất cả session (sid) của một user_id cụ thể."""
    for sid, uid in connected_users.items():
        if str(uid) == str(target_user_id):
            socketio.emit(event_name, data or {}, to=sid)


# ════════════════════════════════════════════════
# HELPER: Lấy user_id từ session hiện tại
# ════════════════════════════════════════════════
def _get_current_user_id():
    return connected_users.get(request.sid)


def _auto_stop_typing(user_id, conversation_id):
    """Server-side timeout: tự broadcast isTyping=False sau TYPING_TIMEOUT giây."""
    key = f"{user_id}_{conversation_id}"
    typing_timers.pop(key, None)
    socketio.emit('user_typing', {
        'conversationId': str(conversation_id),
        'userId': str(user_id),
        'isTyping': False
    }, room=f"conversation_{conversation_id}")


# ════════════════════════════════════════════════
# EVENT: connect
# ════════════════════════════════════════════════
@socketio.on('connect')
def handle_connect(auth=None):
    """
    Xác thực JWT khi client kết nối.
    Client gửi: io(URL, { auth: { token: "Bearer <jwt>" } })
    """
    token = None

    # Lấy token từ auth object (Socket.IO v4+)
    if auth and isinstance(auth, dict):
        token = auth.get('token', '')

    # Fallback: lấy từ query string (?token=xxx)
    if not token:
        token = request.args.get('token', '')

    # Cắt prefix "Bearer " nếu có
    if token and token.startswith('Bearer '):
        token = token[7:]

    if not token:
        print(f'[Socket] Rejected: No token (sid={request.sid})')
        disconnect()
        return False

    try:
        decoded = decode_token(token)
        user_id = decoded['sub']  # flask_jwt_extended lưu identity vào 'sub'
        
        # Cập nhật trạng thái và thời gian hoạt động cuối vào DB
        from datetime import datetime
        user_repo.update(user_id, status='active', last_seen=datetime.utcnow())
        
        connected_users[request.sid] = user_id
        user_rooms[request.sid] = set()
        print(f'[Socket] Connected & Active: user_id={user_id}, sid={request.sid}')
    except Exception as e:
        print(f'[Socket] Rejected: {str(e)}')
        disconnect()
        return False


# ════════════════════════════════════════════════
# EVENT: disconnect
# ════════════════════════════════════════════════
@socketio.on('disconnect')
def handle_disconnect():
    """
    Tự động được gọi khi client mất kết nối.
    Dọn dẹp trạng thái và broadcast typing_stop cho tất cả phòng.
    """
    # 1. Lấy user_id trước khi dọn dẹp
    user_id = connected_users.get(sid)

    if user_id:
        # Broadcast isTyping=False cho tất cả phòng mà user đang ở
        rooms = user_rooms.get(sid, set())
        for room_name in rooms:
            conv_id = room_name.replace("conversation_", "")
            emit('user_typing', {
                'conversationId': conv_id,
                'userId': str(user_id),
                'isTyping': False
            }, room=room_name)

            key = f"{user_id}_{conv_id}"
            timer = typing_timers.pop(key, None)
            if timer:
                timer.cancel()

    # 2. Dọn dẹp bộ nhớ cho sid hiện tại
    connected_users.pop(sid, None)
    user_rooms.pop(sid, None)

    # 3. KIỂM TRA ĐA KẾT NỐI: Chỉ set offline nếu không còn sid nào khác của user này
    if user_id:
        is_still_connected = any(uid == user_id for uid in connected_users.values())
        
        if not is_still_connected:
            from datetime import datetime
            user_repo.update(user_id, status='offline', last_seen=datetime.utcnow())
            print(f'[Socket] Disconnected & Truly Offline: user_id={user_id}')
        else:
            print(f'[Socket] Disconnected one session, but user_id={user_id} still has other active sessions.')


# ════════════════════════════════════════════════
# EVENT: join_conversation
# ════════════════════════════════════════════════
@socketio.on('join_conversation')
def handle_join_room(data):
    """
    Client gửi khi mở/chuyển sang một cuộc hội thoại.
    Payload: { "conversationId": 123 }
    """
    user_id = _get_current_user_id()
    if not user_id:
        emit('error', {'message': 'Unauthorized'})
        return

    conversation_id = data.get('conversationId')
    if not conversation_id:
        emit('error', {'message': 'conversationId is required'})
        return

    # Bảo mật: Kiểm tra user có thực sự là thành viên không
    participant = participant_repo.get_by_conversation_and_user(conversation_id, user_id)
    if not participant:
        emit('error', {'message': 'Bạn không thuộc cuộc hội thoại này.'})
        return

    room_name = f"conversation_{conversation_id}"
    join_room(room_name)

    # Ghi nhận phòng đã tham gia (phục vụ xử lý disconnect)
    if request.sid in user_rooms:
        user_rooms[request.sid].add(room_name)

    print(f'[Socket] user_id={user_id} joined {room_name}')


# ════════════════════════════════════════════════
# EVENT: leave_conversation
# ════════════════════════════════════════════════
@socketio.on('leave_conversation')
def handle_leave_room(data):
    """
    Client gửi khi rời khỏi/chuyển đi cuộc hội thoại khác.
    Payload: { "conversationId": 123 }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return

    conversation_id = data.get('conversationId')
    room_name = f"conversation_{conversation_id}"

    leave_room(room_name)

    # Xóa khỏi danh sách phòng
    if request.sid in user_rooms:
        user_rooms[request.sid].discard(room_name)

    # Hủy timer typing nếu có
    key = f"{user_id}_{conversation_id}"
    timer = typing_timers.pop(key, None)
    if timer:
        timer.cancel()

    print(f'[Socket] user_id={user_id} left {room_name}')


# ════════════════════════════════════════════════
# EVENT: typing_start
# ════════════════════════════════════════════════
@socketio.on('typing_start')
def handle_typing_start(data):
    """
    Client gửi khi người dùng bắt đầu gõ.
    Payload: { "conversationId": 123 }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return

    conversation_id = data.get('conversationId')
    if not conversation_id:
        return

    # Kiểm tra tư cách thành viên
    participant = participant_repo.get_by_conversation_and_user(conversation_id, user_id)
    if not participant:
        return  # Im lặng bỏ qua, không báo lỗi để tránh info leak

    # Lấy tên hiển thị
    user = user_repo.get_by_id(user_id)
    if not user:
        return

    # Reset server-side timeout timer
    key = f"{user_id}_{conversation_id}"
    old_timer = typing_timers.get(key)
    if old_timer:
        old_timer.cancel()

    timer = threading.Timer(TYPING_TIMEOUT, _auto_stop_typing, args=[user_id, conversation_id])
    timer.daemon = True
    timer.start()
    typing_timers[key] = timer

    # Broadcast cho các thành viên khác
    emit('user_typing', {
        'conversationId': str(conversation_id),
        'userId': str(user_id),
        'fullName': user.full_name,
        'isTyping': True
    }, room=f"conversation_{conversation_id}", include_self=False)


# ════════════════════════════════════════════════
# EVENT: typing_stop
# ════════════════════════════════════════════════
@socketio.on('typing_stop')
def handle_typing_stop(data):
    """
    Client gửi khi người dùng dừng gõ (debounce timeout hoặc gửi tin nhắn).
    Payload: { "conversationId": 123 }
    """
    user_id = _get_current_user_id()
    if not user_id:
        return

    conversation_id = data.get('conversationId')
    if not conversation_id:
        return

    # Hủy timer nếu có
    key = f"{user_id}_{conversation_id}"
    timer = typing_timers.pop(key, None)
    if timer:
        timer.cancel()

    emit('user_typing', {
        'conversationId': str(conversation_id),
        'userId': str(user_id),
        'isTyping': False
    }, room=f"conversation_{conversation_id}", include_self=False)
