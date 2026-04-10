from cryptography.fernet import Fernet
from app.config.settings import configs
import base64

class CryptoUtils:
    _fernet = None

    @classmethod
    def get_instance(cls):
        if cls._fernet is None:
            # Fernet key must be 32 url-safe base64-encoded bytes.
            # If the provided key is not in that format, we might need to hash it or encode it.
            key = configs.AES_SECRET_KEY
            if not key:
                raise ValueError("AES_SECRET_KEY is not configured")
            
            # Ensure it's 32 bytes and base64 encoded
            # If it's a plain string, we can use a fixed length seed or just encode it if it fits.
            # But let's assume the .env provides a valid Fernet key for now.
            # If it's a plain password, we should hash it:
            # import hashlib
            # key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
            
            try:
                cls._fernet = Fernet(key.encode() if isinstance(key, str) else key)
            except Exception:
                # Fallback: Hash the key to ensure it's valid for Fernet
                import hashlib
                hashed_key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
                cls._fernet = Fernet(hashed_key)
        return cls._fernet

    @classmethod
    def encrypt(cls, text: str) -> str:
        if not text:
            return text
        fernet = cls.get_instance()
        return fernet.encrypt(text.encode()).decode()

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        if not encrypted_text:
            return encrypted_text
        fernet = cls.get_instance()
        try:
            return fernet.decrypt(encrypted_text.encode()).decode()
        except Exception:
            # If decryption fails, it might not be encrypted or key changed
            return "[Decryption Error]"
