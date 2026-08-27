#!/bin/bash
# 记账Agent部署脚本

set -e

echo "=== 开始部署记账Agent ==="

# 创建项目目录
PROJECT_DIR="/opt/accounting-agent"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 克隆或更新代码
if [ -d ".git" ]; then
    echo "更新代码..."
    git pull origin main
else
    echo "克隆代码..."
    git clone https://github.com/SmallTiger3/accounting-agent.git .
fi

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "错误：请先创建 .env 文件！"
    echo "复制 .env.example 并填入真实配置："
    echo "  cp .env.example .env"
    echo "  vim .env"
    exit 1
fi

# 从.env加载环境变量
source .env

# 更新docker-compose.yml
echo "更新Docker配置..."
cat > docker-compose.yml << EOF
version: '3.8'

services:
  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: \${DATABASE_URL}
      SECRET_KEY: \${SECRET_KEY}
      LLM_PROVIDER: \${LLM_PROVIDER}
      DEEPSEEK_API_KEY: \${DEEPSEEK_API_KEY}
      DEEPSEEK_BASE_URL: \${DEEPSEEK_BASE_URL}
      LLM_MODEL: \${LLM_MODEL}
      LLM_TEMPERATURE: \${LLM_TEMPERATURE}
      CORS_ORIGINS: \${CORS_ORIGINS}
      DEBUG: \${DEBUG}
    ports:
      - "8000:8000"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
EOF

# 构建并启动服务
echo "构建Docker镜像..."
docker-compose build

echo "启动服务..."
docker-compose up -d

echo "=== 部署完成 ==="
echo "前端访问: http://101.200.232.229"
echo "API文档: http://101.200.232.229:8000/docs"