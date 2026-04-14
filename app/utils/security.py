import re

class SecurityUtils:
    # Danh sách từ ngữ nhạy cảm (DLP) - Có thể mở rộng hoặc lưu vào DB/Config
    SENSITIVE_WORDS = [
        r'mật mã', r'password', r'bí mật', r'secret', 
        r'tấn công', r'hack', r'virus', r'malware'
    ]

    # Danh sách từ ngữ độc hại/xúc phạm (Toxicity)
    TOXIC_WORDS = [
        r'ngu', r'vãi', r'chó', r'mẹ', r'đéo', r'cứt', r'cặc', r'lồn', r'đm', r'vcl', r'cc'
    ]

    @classmethod
    def scan_sensitive_content(cls, text: str) -> bool:
        """
        Quét nội dung nhạy cảm sử dụng Regex (DLP).
        """
        if not text: return False
        combined = re.compile('|'.join(cls.SENSITIVE_WORDS), re.IGNORECASE)
        return bool(combined.search(text))

    @classmethod
    def scan_toxic_content(cls, text: str) -> bool:
        """
        Quét từ ngữ độc hại/xúc phạm (Local Filter).
        """
        if not text: return False
        combined = re.compile('|'.join(cls.TOXIC_WORDS), re.IGNORECASE)
        return bool(combined.search(text))
