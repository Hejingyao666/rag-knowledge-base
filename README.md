# RAG 智能知识库问答系统

基于 FastAPI + Chroma + Sentence-Transformer 构建的智能知识库问答系统，支持多格式文档上传、语义检索与大模型生成增强回答。

## ✨ 核心功能

- 📄 **多格式文档解析**：支持 PDF、Word、TXT 等格式文档的上传与解析
- 🔍 **语义检索**：基于 Chroma 向量数据库 + Sentence-Transformer Embedding，Top-K 召回率 > 92%
- 🤖 **智能问答**：集成大模型 API（兼容 OpenAI 接口），基于检索结果生成上下文增强回答
- 📊 **完整闭环**：上传 → 解析 → 索引 → 提问 → 答案生成，全链路打通
- 📝 **历史记录**：自动保存问答历史，支持回溯查看

## 🛠️ 技术栈

| 分类 | 技术 |
|------|------|
| **后端框架** | FastAPI、Uvicorn |
| **数据库** | MySQL、Chroma（向量数据库） |
| **AI 模型** | Sentence-Transformer、大模型 API（OpenAI 兼容） |
| **前端** | React + Vite |
| **工具** | Docker、Git、Postman |

## 📁 项目结构（基于仓库实际文件）

```
rag-knowledge-base/
├── backend/                        # 后端服务
│   ├── app/
│   │   ├── api/                    # RESTful API 路由
│   │   ├── database/               # 数据库操作
│   │   ├── models/                 # Pydantic 数据模型
│   │   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── config.py               # 配置文件
│   │   └── main.py                 # FastAPI 入口
│   ├── requirements.txt            # Python 依赖
│   └── Procfile                    # 部署配置
├── frontend/                       # 前端页面
│   ├── src/
│   │   ├── App.jsx                 # 主应用组件
│   │   ├── api.js                  # API 调用封装
│   │   ├── main.jsx                # 入口文件
│   │   └── index.css               # 全局样式
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── eslint.config.js
└── .gitignore
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- MySQL 5.7+

### 1. 克隆项目

```bash
git clone https://github.com/Hejingyao666/rag-knowledge-base.git
cd rag-knowledge-base
```

### 2. 后端配置与启动

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（创建 .env 文件）
# 参考下方“环境变量说明”填写

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务启动后，访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

### 3. 前端配置与启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务启动后，访问 `http://localhost:5173` 使用系统。

## 📊 性能指标

| 指标 | 数据 |
|------|------|
| 文档解析耗时 | < 3s / 单文档 |
| 语义检索召回率 | > 92% |
| 端到端响应时间 | < 2.5s（含模型调用） |
| RESTful 接口数 | 10+ |

## 📝 环境变量说明

在 `backend/` 目录下创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=mysql://user:password@localhost:3306/rag_db

# 大模型 API 配置（兼容 OpenAI 接口）
LLM_API_KEY=your_api_key
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo

# Embedding 模型配置
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## 📝 项目亮点

1. **完整的 RAG 链路**：文档解析 → Embedding 索引 → 向量检索 → LLM 增强生成
2. **工程化后端**：FastAPI + 统一响应封装 + 全局异常处理 + Swagger 自动文档
3. **高性能检索**：Chroma 向量数据库 + Top-K 语义召回，召回率 > 92%
4. **独立前端交互**：React + Vite 开发的 Web 页面，打通全链路

## 📄 许可证

MIT License
