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

# Bỏ chặn EXPOSE cứng để Railway tự động gán PORT động hoàn toàn (tránh xung đột 502)

# Chạy ứng dụng bằng Gunicorn với Worker Eventlet - Chuẩn Production cho Socket.IO
# Chạy ứng dụng bằng Gunicorn với Worker Gthread (Sử dụng IPv6 [::] để tương thích hoàn toàn với Load Balancer của Railway)
CMD ["sh", "-c", "gunicorn --worker-class gthread -w 2 --threads 50 --bind [::]:${PORT:-8080} --timeout 120 --keep-alive 60 wsgi:app"]
