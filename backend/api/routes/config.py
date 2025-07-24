"""
설정 관련 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from api.dependencies import get_database, get_logger
from config.api_keys import api_keys

router = APIRouter(prefix="/config", tags=["설정"])


class APIKeyRequest(BaseModel):
    """API 키 설정 요청 모델"""
    naver_client_id: Optional[str] = None
    naver_client_secret: Optional[str] = None
    google_api_key: Optional[str] = None
    google_cx: Optional[str] = None


class APIKeyResponse(BaseModel):
    """API 키 설정 응답 모델"""
    success: bool
    message: str
    naver_configured: bool
    google_configured: bool
    timestamp: str


@router.post("/api-keys", response_model=APIKeyResponse)
async def set_api_keys(
    request: APIKeyRequest,
    logger = Depends(get_logger)
):
    """API 키 설정"""
    
    try:
        # 네이버 API 키 설정
        if request.naver_client_id and request.naver_client_secret:
            api_keys.set_naver_keys(request.naver_client_id, request.naver_client_secret)
            logger.info("네이버 API 키가 설정되었습니다.")
        
        # Google API 키 설정
        if request.google_api_key and request.google_cx:
            api_keys.set_google_keys(request.google_api_key, request.google_cx)
            logger.info("Google API 키가 설정되었습니다.")
        
        return APIKeyResponse(
            success=True,
            message="API 키가 성공적으로 설정되었습니다.",
            naver_configured=api_keys.is_naver_configured(),
            google_configured=api_keys.is_google_configured(),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"API 키 설정 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API 키 설정 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/api-keys/status", response_model=APIKeyResponse)
async def get_api_keys_status(
    logger = Depends(get_logger)
):
    """API 키 설정 상태 조회"""
    
    try:
        return APIKeyResponse(
            success=True,
            message="API 키 설정 상태를 조회했습니다.",
            naver_configured=api_keys.is_naver_configured(),
            google_configured=api_keys.is_google_configured(),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"API 키 상태 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API 키 상태 조회 중 오류가 발생했습니다: {str(e)}"
        ) 