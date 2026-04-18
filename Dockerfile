# Sử dụng Python 3.11 làm base image (bản slim để tối ưu dung lượng)
FROM python:3.11-slim

# Cài đặt các thư viện hệ thống cần thiết cho psycopg2 (PostgreSQL) và các C-extensions
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào trước để tận dụng Docker cache
COPY requirements.txt .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào vùng làm việc
COPY . .

# Thiết lập các biến môi trường mặc định (có thể bị ghi đè bởi Fly.io Secrets)
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose cổng 8080 (Fly.io sẽ route traffic vào cổng này)
EXPOSE 8080

# Chạy app bằng Gunicorn kèm eventlet cho phép xử lý WebSocket Socket.IO mượt mà
# Do sử dụng Eventlet, ta chỉ nên dùng 1 worker (-w 1) (hoặc dùng Redis nếu muốn nhiều worker)
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:8080", "run:app"]
