"""
요청 모델 정의
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionCreateRequest(BaseModel):
    """세션 생성 요청"""
    pass


class ChatRequest(BaseModel):
    """채팅 요청"""
    session_id: str = Field(..., description="세션 ID")
    message: str = Field(..., min_length=1, max_length=1000, description="사용자 메시지")


class ProductAnalysisResponse(BaseModel):
    """제품 분석 응답"""
    success: bool
    data: Optional[dict] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.now) 