"""
API 키 설정 파일
"""

import os
from typing import Optional
from utils.logger import logger

class APIKeys:
    """API 키 관리 클래스"""
    
    def __init__(self):
        # 네이버 API 키
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID", "")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        
        # Google API 키 (향후 사용)
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.google_cx = os.getenv("GOOGLE_CX", "")
        
        # API 키 로딩 상태 로깅
        logger.info(f"API 키 로딩 - NAVER_CLIENT_ID: {'설정됨' if self.naver_client_id else '미설정'} (길이: {len(self.naver_client_id) if self.naver_client_id else 0})")
        logger.info(f"API 키 로딩 - NAVER_CLIENT_SECRET: {'설정됨' if self.naver_client_secret else '미설정'} (길이: {len(self.naver_client_secret) if self.naver_client_secret else 0})")
        logger.info(f"API 키 로딩 - GOOGLE_API_KEY: {'설정됨' if self.google_api_key else '미설정'} (길이: {len(self.google_api_key) if self.google_api_key else 0})")
        
        # 환경변수 전체 확인 (디버깅용)
        env_vars = {k: v for k, v in os.environ.items() if 'NAVER' in k or 'GOOGLE' in k}
        logger.info(f"관련 환경변수: {env_vars}")
    
    def get_naver_keys(self) -> tuple[str, str]:
        """네이버 API 키 반환"""
        return self.naver_client_id, self.naver_client_secret
    
    def get_google_keys(self) -> tuple[str, str]:
        """Google API 키 반환"""
        return self.google_api_key, self.google_cx
    
    def set_naver_keys(self, client_id: str, client_secret: str):
        """네이버 API 키 설정"""
        self.naver_client_id = client_id
        self.naver_client_secret = client_secret
        # 환경 변수로도 설정
        os.environ["NAVER_CLIENT_ID"] = client_id
        os.environ["NAVER_CLIENT_SECRET"] = client_secret
        logger.info(f"네이버 API 키 설정 완료 - Client ID: {client_id[:5]}..., Secret: {client_secret[:5]}...")
    
    def set_google_keys(self, api_key: str, cx: str):
        """Google API 키 설정"""
        self.google_api_key = api_key
        self.google_cx = cx
        # 환경 변수로도 설정
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GOOGLE_CX"] = cx
        logger.info(f"Google API 키 설정 완료 - API Key: {api_key[:5]}..., CX: {cx[:5]}...")
    
    def is_naver_configured(self) -> bool:
        """네이버 API 키가 설정되었는지 확인"""
        return bool(self.naver_client_id and self.naver_client_secret)
    
    def is_google_configured(self) -> bool:
        """Google API 키가 설정되었는지 확인"""
        return bool(self.google_api_key and self.google_cx)


# 전역 API 키 인스턴스
api_keys = APIKeys() 