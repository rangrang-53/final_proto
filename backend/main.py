"""
FastAPI 메인 애플리케이션
"""

import os
import sys

# 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config.settings import settings
from utils.logger import logger
from api.routes import health, upload, session, product, chat, config
from core.agent.agent_core import initialize_agent
from services.simple_product_search_service import simple_product_search_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("🚀 백엔드 서버가 시작됩니다...")
    logger.info(f"서버 주소: http://{settings.backend_host}:{settings.backend_port}")
    
    # 네이버 API 키 설정
    if settings.naver_client_id and settings.naver_client_secret:
        simple_product_search_service.set_api_keys(
            naver_client_id=settings.naver_client_id,
            naver_client_secret=settings.naver_client_secret
        )
        logger.info("✅ 네이버 API 키가 설정되었습니다.")
    else:
        logger.warning("⚠️ 네이버 API 키가 설정되지 않았습니다. 모의 검색 모드로 실행됩니다.")
    
    # AI Agent 초기화
    await initialize_agent()
    
    yield
    
    # 종료 시
    logger.info("🛑 백엔드 서버를 종료합니다...")


# FastAPI 앱 생성
app = FastAPI(
    title="5060 중장년층 가전제품 사용법 안내 Agent",
    description="AI 기반 가전제품 사용법 안내 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(product.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(config.router, prefix="/api")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "5060 중장년층 가전제품 사용법 안내 Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True,
        log_config=None  # 기본 로그 설정 사용
    ) 