from app import create_app
from app.services.auth_service import AuthService

app = create_app()
with app.app_context():
    service = AuthService()
    try:
        res = service.register_user({
            "email": "testdirect@example.com",
            "password": "Password123!",
            "fullName": "Direct Test",
            "phone": "0987654321"
        })
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()
