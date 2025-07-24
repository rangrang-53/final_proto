"""
세션 관리 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import uuid

from api.dependencies import get_database, get_logger, validate_session
from config.database import MemoryDatabase
from models.request_models import SessionCreateRequest


router = APIRouter(prefix="/session", tags=["session"])


@router.post("/create")
async def create_session(
    request: SessionCreateRequest = None,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """새 세션 생성"""
    
    session_id = str(uuid.uuid4())
    
    try:
        session_data = db.create_session(session_id)
        
        logger.info(f"새 세션 생성: {session_id}")
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "created_at": session_data["created_at"].isoformat(),
                "expires_at": session_data["expires_at"].isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"세션 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="세션 생성 중 오류가 발생했습니다."
        )


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """세션 정보 조회"""
    
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    # 민감한 정보 제외하고 반환
    return {
        "success": True,
        "data": {
            "session_id": session["session_id"],
            "created_at": session["created_at"].isoformat(),
            "expires_at": session["expires_at"].isoformat(),
            "has_product_info": session["product_info"] is not None,
            "has_uploaded_image": "uploaded_image" in session,
            "chat_message_count": len(session["chat_history"])
        },
        "timestamp": datetime.now().isoformat()
    }


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """세션 삭제"""
    
    # 세션 존재 확인
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    try:
        # 임시 파일 정리
        from utils.file_utils import cleanup_temp_file
        temp_files = session.get("temp_files", [])
        for file_path in temp_files:
            cleanup_temp_file(file_path)
        
        # 세션 삭제
        db.delete_session(session_id)
        
        logger.info(f"세션 삭제 완료: {session_id}")
        
        return {
            "success": True,
            "data": {
                "message": "세션이 성공적으로 삭제되었습니다."
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"세션 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="세션 삭제 중 오류가 발생했습니다."
        )


@router.post("/cleanup")
async def cleanup_expired_sessions(
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """만료된 세션 정리"""
    
    try:
        cleaned_count = db.cleanup_expired_sessions()
        
        logger.info(f"만료된 세션 정리 완료: {cleaned_count}개")
        
        return {
            "success": True,
            "data": {
                "cleaned_sessions": cleaned_count,
                "message": f"{cleaned_count}개의 만료된 세션이 정리되었습니다."
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"세션 정리 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="세션 정리 중 오류가 발생했습니다."
        ) 