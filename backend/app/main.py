# FastAPI Application Entry Point
# FastAPI 应用程序入口点

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import os

from app.api.routes import router
from app.log import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events.
    应用程序生命周期事件。

    Args:
        app: FastAPI application instance.
            FastAPI 应用程序实例。
    """
    # Startup
    # 启动
    logger.info("Starting mini-agent API...")
    yield
    # Shutdown
    # 关闭
    logger.info("Shutting down mini-agent API...")


# Create FastAPI application
# 创建 FastAPI 应用程序
app = FastAPI(
    title="Mini-Agent API",
    description="Simple agent framework API for local agent learning and research",
    version="0.1.0",
    lifespan=lifespan
)


# Add CORS middleware
# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
# 包含 API 路由
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint.
    根端点。

    Returns:
        Welcome message.
            欢迎消息。
    """
    return {"message": "Welcome to Mini-Agent API", "version": "0.1.0"}


# For running with uvicorn directly
# 用于直接使用 uvicorn 运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=True
    )