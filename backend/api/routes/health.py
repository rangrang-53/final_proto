"""
상태 확인 API
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from api.dependencies import get_database, get_logger
from config.database import MemoryDatabase


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check(
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """시스템 상태 확인"""
    
    logger.info("Health check 요청")
    
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "memory_db": "running",
                "session_count": db.get_session_count()
            }
        },
        "timestamp": datetime.now().isoformat()
    } 