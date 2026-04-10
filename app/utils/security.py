import re

class SecurityUtils:
    # Danh sách từ ngữ nhạy cảm (DLP) - Có thể mở rộng hoặc lưu vào DB/Config
    SENSITIVE_WORDS = [
        r'mật mã', r'password', r'bí mật', r'secret', 
        r'tấn công', r'hack', r'virus', r'malware'
    ]

    @classmethod
    def scan_sensitive_content(cls, text: str) -> bool:
        """
        Quét nội dung nhạy cảm sử dụng Regex (DLP).
        Trả về True nếu phát hiện nội dung nhạy cảm.
        """
        if not text:
            return False
            
        combined_regex = re.compile('|'.join(cls.SENSITIVE_WORDS), re.IGNORECASE)
        return bool(combined_regex.search(text))
