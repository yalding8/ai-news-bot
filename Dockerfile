FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 默认运行企业微信推送 (可通过环境变量修改)
CMD ["python3", "scheduler.py", "--check"]