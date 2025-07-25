"""
API 키 설정 페이지
"""

import streamlit as st
import requests
from typing import Dict, Any
import json

from services.api_client import get_api_client
from utils.constants import BACKEND_BASE_URL


def render_config_page():
    """API 키 설정 페이지 렌더링"""
    
    st.title("🔧 API 키 설정")
    st.markdown("---")
    
    # 현재 API 키 상태 조회
    status_data = get_api_keys_status()
    
    if status_data:
        st.subheader("📊 현재 설정 상태")
        col1, col2 = st.columns(2)
        
        with col1:
            if status_data.get("naver_configured"):
                st.success("✅ 네이버 API 키 설정됨")
            else:
                st.error("❌ 네이버 API 키 미설정")
        
        with col2:
            if status_data.get("google_configured"):
                st.success("✅ Google API 키 설정됨")
            else:
                st.error("❌ Google API 키 미설정")
    
    st.markdown("---")
    
    # API 키 설정 폼
    st.subheader("🔑 API 키 설정")
    
    with st.form("api_keys_form"):
        st.markdown("### 네이버 API 키")
        st.info("네이버 개발자 센터(https://developers.naver.com)에서 발급받은 API 키를 입력하세요.")
        
        naver_client_id = st.text_input(
            "네이버 클라이언트 ID",
            type="password",
            help="네이버 애플리케이션의 클라이언트 ID"
        )
        
        naver_client_secret = st.text_input(
            "네이버 클라이언트 시크릿",
            type="password",
            help="네이버 애플리케이션의 클라이언트 시크릿"
        )
        
        st.markdown("### Google API 키 (선택사항)")
        st.info("Google Custom Search API 키가 있다면 입력하세요.")
        
        google_api_key = st.text_input(
            "Google API 키",
            type="password",
            help="Google Custom Search API 키"
        )
        
        google_cx = st.text_input(
            "Google Custom Search Engine ID",
            type="password",
            help="Google Custom Search Engine ID"
        )
        
        submitted = st.form_submit_button("🔧 API 키 설정")
        
        if submitted:
            if naver_client_id and naver_client_secret:
                result = set_api_keys(
                    naver_client_id=naver_client_id,
                    naver_client_secret=naver_client_secret,
                    google_api_key=google_api_key if google_api_key else None,
                    google_cx=google_cx if google_cx else None
                )
                
                if result and result.get("success"):
                    st.success("✅ API 키가 성공적으로 설정되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ API 키 설정에 실패했습니다.")
            else:
                st.warning("⚠️ 네이버 클라이언트 ID와 시크릿을 입력해주세요.")
    
    st.markdown("---")
    
    # API 키 테스트
    st.subheader("🧪 API 키 테스트")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 네이버 API 테스트"):
            test_result = test_naver_api()
            if test_result and test_result.get("success"):
                st.success("✅ 네이버 API 키가 정상적으로 작동합니다!")
                st.json(test_result)
            else:
                st.error("❌ 네이버 API 키 테스트 실패")
                if test_result:
                    st.error(f"오류: {test_result.get('error', '알 수 없는 오류')}")
                    if test_result.get('error_details'):
                        st.text_area("상세 오류 정보", test_result['error_details'], height=100)
    
    with col2:
        if st.button("🔄 API 키 상태 새로고침"):
            st.rerun()
    
    st.markdown("---")
    
    # 도움말
    st.subheader("📖 API 키 발급 방법")
    
    with st.expander("네이버 API 키 발급 방법"):
        st.markdown("""
        1. **네이버 개발자 센터 접속**
           - https://developers.naver.com 접속
        
        2. **애플리케이션 등록**
           - 로그인 후 "애플리케이션 등록" 클릭
        
        3. **애플리케이션 정보 입력**
           - 애플리케이션 이름: 원하는 이름 입력
           - 사용 API: "검색" 선택
           - 비로그인 오픈 API 서비스 환경: "웹 서비스 URL" 입력
             - 개발 중이라면: `http://localhost:8501`
             - 배포 후라면: 실제 도메인 URL
        
        4. **API 키 확인**
           - 등록 완료 후 "애플리케이션 정보"에서 확인
           - Client ID와 Client Secret 복사
        
        5. **위 폼에 입력**
           - Client ID와 Client Secret을 위 폼에 입력 후 설정
        """)
    
    with st.expander("Google API 키 발급 방법 (선택사항)"):
        st.markdown("""
        1. **Google Cloud Console 접속**
           - https://console.cloud.google.com 접속
        
        2. **프로젝트 생성/선택**
           - 새 프로젝트 생성 또는 기존 프로젝트 선택
        
        3. **Custom Search API 활성화**
           - "API 및 서비스" > "라이브러리"에서 "Custom Search API" 검색 후 활성화
        
        4. **사용자 인증 정보 생성**
           - "API 및 서비스" > "사용자 인증 정보"에서 "사용자 인증 정보 만들기" > "API 키"
        
        5. **Custom Search Engine 생성**
           - https://cse.google.com/cse/ 접속
           - 새 검색 엔진 생성
           - 검색 엔진 ID(CX) 복사
        
        6. **위 폼에 입력**
           - API 키와 검색 엔진 ID를 위 폼에 입력
        """)


def test_naver_api() -> Dict[str, Any]:
    """네이버 API 키 테스트"""
    try:
        client = get_api_client()
        response = client.get(f"{BACKEND_BASE_URL}/api/config/test-naver-api")
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 테스트 요청 실패: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"API 테스트 중 오류: {str(e)}")
        return None


def get_api_keys_status() -> Dict[str, Any]:
    """API 키 설정 상태 조회"""
    try:
        client = get_api_client()
        response = client.get(f"{BACKEND_BASE_URL}/api/config/api-keys/status")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 키 상태 조회 실패: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"API 키 상태 조회 중 오류: {str(e)}")
        return None


def set_api_keys(
    naver_client_id: str = None,
    naver_client_secret: str = None,
    google_api_key: str = None,
    google_cx: str = None
) -> Dict[str, Any]:
    """API 키 설정"""
    try:
        data = {}
        if naver_client_id and naver_client_secret:
            data["naver_client_id"] = naver_client_id
            data["naver_client_secret"] = naver_client_secret
        if google_api_key and google_cx:
            data["google_api_key"] = google_api_key
            data["google_cx"] = google_cx
        
        client = get_api_client()
        response = client.post(
            f"{BACKEND_BASE_URL}/api/config/api-keys",
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 키 설정 실패: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"API 키 설정 중 오류: {str(e)}")
        return None 