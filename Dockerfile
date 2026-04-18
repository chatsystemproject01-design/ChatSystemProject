# Sử dụng Python 3.11 - Phiên bản ổn định nhất cho Socket.IO và Eventlet
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (cho psycopg2 và các build tool)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Thiết lập biến môi trường
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port mặc định để Railway định tuyến traffic chuẩn xác
EXPOSE 8080

# Chạy bằng worker 'sync' (Chuẩn nhất để debug 502) và bỏ --preload để tránh lỗi fork không báo trước
CMD ["sh", "-c", "gunicorn -w 4 --bind 0.0.0.0:${PORT:-8080} --timeout 120 --access-logfile - --error-logfile - wsgi:app"]
