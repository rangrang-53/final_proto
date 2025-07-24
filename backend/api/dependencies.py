"""
API 의존성 주입
"""

from fastapi import Depends, HTTPException, status
from config.database import memory_db
from utils.logger import logger


def get_database():
    """데이터베이스 의존성"""
    return memory_db


def get_logger():
    """로거 의존성"""
    return logger


async def validate_session(session_id: str, db = Depends(get_database)):
    """세션 유효성 검사"""
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    return session 