import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.db import init_db
from app.api import documents, chat

app = FastAPI(
    title="RAG 知识库问答系统",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)

os.makedirs(settings.UPLOAD_DIR,        exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)


@app.on_event("startup")
async def startup():
    init_db()
    print("✅ 数据库初始化完成")
    print(f"✅ 上传目录: {settings.UPLOAD_DIR}")
    print(f"✅ 向量库目录: {settings.CHROMA_PERSIST_DIR}")


@app.get("/")
def root():
    return {"status": "running", "message": "RAG系统已启动 🚀", "docs": "/docs"}