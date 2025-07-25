"""
환경 설정 관리
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API 키
    google_api_key: str = ""
    langsmith_api_key: str = ""
    naver_client_id: str = ""  # 네이버 클라이언트 ID
    naver_client_secret: str = ""  # 네이버 클라이언트 시크릿
    
    # 서버 설정
    backend_host: str = "localhost"
    backend_port: int = 8000
    frontend_host: str = "localhost"
    frontend_port: int = 8501
    
    # CORS 설정
    allowed_origins: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]
    
    # 파일 업로드 설정
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: str = "jpg,jpeg,png,webp"
    upload_dir: str = "temp/uploads"
    
    # 세션 설정
    session_expire_hours: int = 1
    
    # 로깅 설정
    log_level: str = "INFO"
    
    # AI 설정
    gemini_model: str = "gemini-2.5-flash-preview-05-20"
    max_tokens: int = 8192
    temperature: float = 0.7
    
    class Config:
        # 프로젝트 루트의 .env 파일 참조
        env_file = [
            ".env",  # 현재 디렉토리
            "../.env",  # 프로젝트 루트
        ]
        case_sensitive = False
        extra = "allow"  # 추가 필드 허용


# 전역 설정 인스턴스
settings = Settings()

# 환경 변수에서 직접 로드 (우선순위)
if os.getenv("GOOGLE_API_KEY"):
    settings.google_api_key = os.getenv("GOOGLE_API_KEY")
if os.getenv("LANGSMITH_API_KEY"):
    settings.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
if os.getenv("NAVER_CLIENT_ID"):
    settings.naver_client_id = os.getenv("NAVER_CLIENT_ID")
if os.getenv("NAVER_CLIENT_SECRET"):
    settings.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET") 