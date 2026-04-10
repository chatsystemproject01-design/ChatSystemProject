from supabase import create_client, Client
from app.config.settings import configs
import filetype
import os
import uuid

class MediaStorage:
    _client: Client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            # Loại bỏ khoảng trắng thừa nếu có trong file .env
            url = configs.SUPABASE_URL.strip()
            key = configs.SUPABASE_KEY.strip()
            cls._client = create_client(url, key)
        return cls._client

    @classmethod
    def validate_file(cls, file_stream):
        """
        Kiểm tra Magic Bytes và định dạng file an toàn.
        Chặn .exe, .js, .bat và các file không xác định.
        Giới hạn 20MB.
        """
        # 1. Kiểm tra kích thước (20MB)
        file_stream.seek(0, os.SEEK_END)
        size = file_stream.tell()
        file_stream.seek(0)
        
        if size > 20 * 1024 * 1024:
            return False, "Kích thước file quá lớn (tối đa 20MB)."

        # 2. Kiểm tra Magic Bytes
        kind = filetype.guess(file_stream.read(2048))
        file_stream.seek(0) # Reset stream sau khi đọc head

        if kind is None:
            return False, "Định dạng file không xác định hoặc không an toàn."

        # Danh sách các định dạng bị cấm (dựa trên MIME hoặc extension)
        forbidden_mimes = ['application/x-msdownload', 'application/javascript', 'text/javascript']
        forbidden_exts = ['exe', 'js', 'bat', 'sh', 'msi']

        if kind.mime in forbidden_mimes or kind.extension in forbidden_exts:
            return False, f"Loại file .{kind.extension} không được phép tải lên."

        return True, kind

    @classmethod
    def upload_file(cls, file_stream, filename):
        """
        Upload file lên Supabase Storage.
        """
        client = cls.get_client()
        bucket = configs.SUPABASE_STORAGE_BUCKET
        
        # Tạo tên file duy nhất để tránh trùng lặp (chỉ giữ lại phần mở rộng an toàn)
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            ext = f".{filetype.guess_extension(content) or 'bin'}"
            
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # Read file content
        content = file_stream.read()
        
        try:
            mime = filetype.guess_mime(content) or "application/octet-stream"
            res = client.storage.from_(bucket).upload(
                path=unique_filename,
                file=content,
                file_options={"content-type": mime}
            )
            
            # Lấy Public URL (Giả sử bucket là Public)
            url = client.storage.from_(bucket).get_public_url(unique_filename)
            return {
                "url": url,
                "filename": unique_filename,
                "size": len(content)
            }
        except Exception as e:
            raise Exception(f"Lỗi upload Supabase: {str(e)}")
