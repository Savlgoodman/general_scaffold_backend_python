"""
FastAPI 应用主入口
"""
import uvicorn
from app.core.app import create_app
from app.core.config import settings

# 创建FastAPI应用实例
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.reload,
        log_level=settings.logging.level.lower()
    )

