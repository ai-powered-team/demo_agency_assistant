"""
AI 保险数字分身项目主入口文件

基于 FastAPI + LangGraph 构建的智能保险推荐服务。
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from util import config, logger
from api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("AI 保险数字分身服务启动中...")

    # 验证配置
    try:
        config.validate()
        logger.info("配置验证通过")
    except ValueError as e:
        logger.error(f"配置验证失败: {e}")
        raise

    logger.info(f"服务将在 {config.HOST}:{config.PORT} 启动")

    yield

    # 关闭时的清理
    logger.info("AI 保险数字分身服务关闭中...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""

    app = FastAPI(
        title="AI 保险数字分身",
        description="基于 LangGraph 的智能保险推荐服务",
        version="1.0.0",
        lifespan=lifespan
    )

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS.split(
            ",") if config.CORS_ORIGINS != "*" else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(router, prefix="/api/v1")

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return JSONResponse(
            content={
                "status": "healthy",
                "service": "AI 保险数字分身",
                "version": "1.0.0"
            }
        )

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # 本地开发时直接运行
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
