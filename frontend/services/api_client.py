"""
프론트엔드-백엔드 통신 API 클라이언트
"""

import requests
import time
from typing import Dict, Any, Optional, List
from utils.constants import API_ENDPOINTS
import streamlit as st


class APIClient:
    """백엔드 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.timeout = 30
        self.max_retries = 3
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """HTTP 요청 수행 (재시도 로직 포함)"""
        
        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json(),
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
                    
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": "요청 시간이 초과되었습니다.",
                        "status_code": 408
                    }
                time.sleep(1)  # 재시도 전 대기
                
            except requests.exceptions.ConnectionError:
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": "백엔드 서버에 연결할 수 없습니다.",
                        "status_code": 503
                    }
                time.sleep(2)  # 재시도 전 대기
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"요청 처리 중 오류 발생: {str(e)}",
                    "status_code": 500
                }
        
        return {
            "success": False,
            "error": "최대 재시도 횟수를 초과했습니다.",
            "status_code": 500
        }
    
    def health_check(self) -> Dict[str, Any]:
        """서버 상태 확인"""
        return self._make_request("GET", f"{self.base_url}/api/health")
    
    # 세션 관리
    def create_session(self) -> Dict[str, Any]:
        """새 세션 생성"""
        return self._make_request("POST", f"{self.base_url}/api/session/create")
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """세션 정보 조회"""
        return self._make_request("GET", f"{self.base_url}/api/session/{session_id}")
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """세션 삭제"""
        return self._make_request("DELETE", f"{self.base_url}/api/session/{session_id}")
    
    # 이미지 업로드
    def upload_image(self, file_data: bytes, filename: str, session_id: str = None) -> Dict[str, Any]:
        """이미지 파일 업로드"""
        files = {"file": (filename, file_data, "image/jpeg")}
        data = {}
        if session_id:
            data["session_id"] = session_id
        return self._make_request("POST", f"{self.base_url}/api/upload/image", files=files, data=data)
    
    def get_upload_status(self, session_id: str) -> Dict[str, Any]:
        """업로드 상태 조회"""
        return self._make_request("GET", f"{self.base_url}/api/upload/status/{session_id}")
    
    # 제품 인식
    def analyze_product(self, session_id: str) -> Dict[str, Any]:
        """제품 분석 시작"""
        return self._make_request("POST", f"{self.base_url}/api/product/analyze/{session_id}")
    
    def get_analysis_result(self, session_id: str) -> Dict[str, Any]:
        """제품 분석 결과 조회"""
        return self._make_request("GET", f"{self.base_url}/api/product/analyze/{session_id}/result")
    
    def reanalyze_product(self, session_id: str) -> Dict[str, Any]:
        """제품 재분석"""
        return self._make_request("POST", f"{self.base_url}/api/product/analyze/{session_id}/retry")
    
    def get_product_categories(self) -> Dict[str, Any]:
        """지원 제품 카테고리 조회"""
        return self._make_request("GET", f"{self.base_url}/api/product/categories")
    
    def get_product_status(self, session_id: str) -> Dict[str, Any]:
        """제품 분석 상태 확인"""
        return self._make_request("GET", f"{self.base_url}/api/product/status/{session_id}")
    
    # 채팅
    def send_chat_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """채팅 메시지 전송"""
        data = {
            "session_id": session_id,
            "message": message
        }
        return self._make_request("POST", f"{self.base_url}/api/chat/{session_id}", json=data)
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """채팅 히스토리 조회"""
        params = {"limit": limit}
        return self._make_request("GET", f"{self.base_url}/api/chat/{session_id}/history", params=params)
    
    def clear_chat_history(self, session_id: str) -> Dict[str, Any]:
        """채팅 히스토리 초기화"""
        return self._make_request("DELETE", f"{self.base_url}/api/chat/{session_id}/history")
    
    def get_suggested_questions(self, session_id: str) -> Dict[str, Any]:
        """추천 질문 조회"""
        return self._make_request("GET", f"{self.base_url}/api/chat/{session_id}/suggestions")
    
    def get_chat_statistics(self, session_id: str) -> Dict[str, Any]:
        """채팅 통계 조회"""
        return self._make_request("GET", f"{self.base_url}/api/chat/{session_id}/statistics")
    
    def get_chat_status(self, session_id: str) -> Dict[str, Any]:
        """채팅 상태 확인"""
        return self._make_request("GET", f"{self.base_url}/api/chat/{session_id}/status")


# 전역 API 클라이언트 인스턴스
@st.cache_resource
def get_api_client() -> APIClient:
    """API 클라이언트 인스턴스 반환 (캐시됨)"""
    return APIClient()


# 편의 함수들
def check_backend_connection() -> bool:
    """백엔드 서버 연결 상태 확인"""
    try:
        client = get_api_client()
        result = client.health_check()
        return result["success"]
    except Exception:
        return False


def get_or_create_session() -> Optional[str]:
    """세션 ID 가져오기 또는 생성"""
    
    # 세션 상태에서 기존 세션 ID 확인
    if "session_id" in st.session_state:
        session_id = st.session_state.session_id
        return session_id  # 세션이 있으면 바로 반환 (유효성 검사 생략)
    
    # 새 세션 생성
    client = get_api_client()
    result = client.create_session()
    
    if result["success"]:
        session_id = result["data"]["data"]["session_id"]
        st.session_state.session_id = session_id
        return session_id
    
    return None


def handle_api_error(result: Dict[str, Any], default_message: str = "오류가 발생했습니다.") -> str:
    """API 오류 처리 및 사용자 친화적 메시지 반환"""
    
    if result["success"]:
        return ""
    
    error = result.get("error", default_message)
    status_code = result.get("status_code", 500)
    
    if status_code == 503:
        return "🔌 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요."
    elif status_code == 408:
        return "⏱️ 요청 시간이 초과되었습니다. 다시 시도해 주세요."
    elif status_code == 404:
        return "❌ 요청한 정보를 찾을 수 없습니다."
    elif status_code == 400:
        return f"⚠️ {error}"
    else:
        return f"🚨 {error}"


def wait_for_analysis_completion(session_id: str, max_wait_time: int = 120) -> Dict[str, Any]:
    """제품 분석 완료까지 대기 (폴링)"""
    
    client = get_api_client()
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        result = client.get_analysis_result(session_id)
        
        if result["success"]:
            data = result["data"]
            if isinstance(data, dict) and "data" in data:
                # 분석 완료된 경우
                if "product_info" in data["data"]:
                    return result
                # 아직 분석 중인 경우
                elif data["data"].get("status") == "analyzing":
                    time.sleep(3)  # 3초 대기 후 다시 확인
                    continue
        
        # 오류가 발생한 경우
        return result
    
    # 시간 초과
    return {
        "success": False,
        "error": "분석 시간이 초과되었습니다. 다시 시도해 주세요.",
        "status_code": 408
    } 