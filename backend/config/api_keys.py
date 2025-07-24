"""
API 키 설정 파일
"""

import os
from typing import Optional

class APIKeys:
    """API 키 관리 클래스"""
    
    def __init__(self):
        # 네이버 API 키
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID", "")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        
        # Google API 키 (향후 사용)
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.google_cx = os.getenv("GOOGLE_CX", "")
    
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
    
    def set_google_keys(self, api_key: str, cx: str):
        """Google API 키 설정"""
        self.google_api_key = api_key
        self.google_cx = cx
        # 환경 변수로도 설정
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GOOGLE_CX"] = cx
    
    def is_naver_configured(self) -> bool:
        """네이버 API 키가 설정되었는지 확인"""
        return bool(self.naver_client_id and self.naver_client_secret)
    
    def is_google_configured(self) -> bool:
        """Google API 키가 설정되었는지 확인"""
        return bool(self.google_api_key and self.google_cx)


# 전역 API 키 인스턴스
api_keys = APIKeys() 