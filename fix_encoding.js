const fs = require('fs');
const path = require('path');
function w(rel, content) {
  const p = path.join('D:/gpl/agent', rel);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content, 'utf8');
  console.log('OK: ' + rel);
}

// README.md
w('README.md', `# 记账Agent

智能AI记账助手 - 基于LangChain的个人财务管理应用

## ✨ 功能特性

- 🤖 **AI对话记账** - 用自然语言记录收支，如"今天午餐花了35元"
- 📊 **智能分类** - 自动识别并分类交易
- 📈 **消费分析** - 按时间、分类统计消费情况
- ⚠️ **预算提醒** - 超支自动预警
- 💡 **财务建议** - 基于消费模式的个性化建议
- 📱 **响应式Web** - 支持桌面和移动端访问

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + TypeScript + Element Plus + ECharts |
| **后端** | FastAPI + SQLAlchemy + Alembic |
| **数据库** | PostgreSQL |
| **AI框架** | LangChain + DeepSeek |
| **部署** | Docker + Nginx |

## 🚀 快速开始

### 方式一：Docker部署（推荐）

1. 克隆项目
\`\`\`bash
git clone https://github.com/SmallTiger3/accounting-agent.git
cd accounting-agent
\`\`\`

2. 配置环境变量
\`\`\`bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
\`\`\`

3. 启动服务
\`\`\`bash
docker-compose up -d
\`\`\`

4. 访问应用
- 前端：http://localhost
- API文档：http://localhost:8000/docs

### 方式二：本地开发

#### 后端

\`\`\`bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\\Scripts\\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

#### 前端

\`\`\`bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
\`\`\`

## 📁 项目结构

\`\`\`
accounting-agent/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   └── endpoints/     # 各模块端点
│   │   ├── agent/             # LangChain Agent
│   │   │   ├── tools/         # Agent工具
│   │   │   ├── accounting_agent.py
│   │   │   └── llm_factory.py
│   │   ├── core/              # 核心配置
│   │   ├── db/                # 数据库连接
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic模式
│   │   └── main.py            # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── api/               # API调用
│   │   ├── components/        # 组件
│   │   ├── layouts/           # 布局
│   │   ├── router/            # 路由
│   │   ├── stores/            # 状态管理
│   │   └── views/             # 页面
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
\`\`\`

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| \`DATABASE_URL\` | PostgreSQL连接字符串 | - |
| \`SECRET_KEY\` | JWT密钥 | - |
| \`LLM_PROVIDER\` | LLM提供商 | \`deepseek\` |
| \`DEEPSEEK_API_KEY\` | DeepSeek API密钥 | - |
| \`DEEPSEEK_BASE_URL\` | DeepSeek API地址 | \`https://api.deepseek.com\` |
| \`LLM_MODEL\` | 模型名称 | \`deepseek-chat\` |
| \`LLM_TEMPERATURE\` | 生成温度 | \`0.7\` |

### 支持的LLM

- **DeepSeek** - 推荐，性价比高
- **OpenAI GPT-4o** - 效果最好，价格较贵
- **MiMo** - 小米自研模型（需配置API地址）

## 📖 API文档

启动后端服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
`);

console.log('Done: README.md');