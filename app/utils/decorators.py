from functools import wraps
from flask_jwt_extended import get_jwt
from app.utils.exceptions import ForbiddenError

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") != "Admin":
                raise ForbiddenError("Quyền truy cập bị từ chối. Yêu cầu quyền Admin.")
            return fn(*args, **kwargs)
        return decorator
    return wrapper
