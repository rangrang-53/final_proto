"""
채팅 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from api.dependencies import get_database, get_logger
from config.database import MemoryDatabase
from services.chat_service import get_chat_service
from models.request_models import ChatRequest


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{session_id}")
async def send_message(
    session_id: str,
    request: ChatRequest,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """채팅 메시지 전송"""
    
    logger.info(f"채팅 메시지 전송: session_id={session_id}, message={request.message[:50]}...")
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    # 요청 세션 ID와 URL 세션 ID 일치 확인
    if request.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="세션 ID가 일치하지 않습니다."
        )
    
    try:
        chat_service = get_chat_service()
        result = await chat_service.send_message(session_id, request.message)
        
        if result["success"]:
            return result
        else:
            # 제품 분석이 완료되지 않은 경우 등의 비즈니스 오류
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 메시지 전송 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="채팅 메시지 전송 중 오류가 발생했습니다."
        )


@router.get("/{session_id}/history")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """채팅 히스토리 조회"""
    
    logger.info(f"채팅 히스토리 조회: session_id={session_id}, limit={limit}")
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    try:
        chat_service = get_chat_service()
        result = chat_service.get_chat_history(session_id, limit)
        
        return result
        
    except Exception as e:
        logger.error(f"채팅 히스토리 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="채팅 히스토리 조회 중 오류가 발생했습니다."
        )


@router.delete("/{session_id}/history")
async def clear_chat_history(
    session_id: str,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """채팅 히스토리 초기화"""
    
    logger.info(f"채팅 히스토리 초기화: session_id={session_id}")
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    try:
        chat_service = get_chat_service()
        result = chat_service.clear_chat_history(session_id)
        
        return result
        
    except Exception as e:
        logger.error(f"채팅 히스토리 초기화 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="채팅 히스토리 초기화 중 오류가 발생했습니다."
        )


@router.get("/{session_id}/suggestions")
async def get_suggested_questions(
    session_id: str,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """추천 질문 조회"""
    
    logger.info(f"추천 질문 조회: session_id={session_id}")
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    try:
        chat_service = get_chat_service()
        result = chat_service.get_suggested_questions(session_id)
        
        return result
        
    except Exception as e:
        logger.error(f"추천 질문 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="추천 질문 조회 중 오류가 발생했습니다."
        )


@router.get("/{session_id}/statistics")
async def get_chat_statistics(
    session_id: str,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """채팅 통계 조회"""
    
    logger.info(f"채팅 통계 조회: session_id={session_id}")
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    try:
        chat_service = get_chat_service()
        result = chat_service.get_chat_statistics(session_id)
        
        return result
        
    except Exception as e:
        logger.error(f"채팅 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="채팅 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/{session_id}/status")
async def get_chat_status(
    session_id: str,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """채팅 상태 확인"""
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    # 상태 정보 구성
    has_product_info = session.get("product_info") is not None
    chat_history = session.get("chat_history", [])
    total_messages = len(chat_history)
    last_chat_at = session.get("last_chat_at", "")
    
    if has_product_info:
        if total_messages > 0:
            status = "active"
            message = "채팅이 활성 상태입니다."
        else:
            status = "ready"
            message = "채팅을 시작할 수 있습니다."
    else:
        status = "waiting"
        message = "제품 분석을 먼저 완료해 주세요."
    
    return {
        "success": True,
        "data": {
            "status": status,
            "message": message,
            "has_product_info": has_product_info,
            "total_messages": total_messages,
            "last_chat_at": last_chat_at,
            "session_id": session_id
        },
        "timestamp": datetime.now().isoformat()
    } 