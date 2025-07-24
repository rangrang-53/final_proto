"""
분석 진행 페이지
"""

import streamlit as st
import time
from typing import Dict, Any, Optional

from utils.ui_utils import show_header, show_error_message, show_success_message
from services.api_client import get_api_client, handle_api_error, wait_for_analysis_completion
from services.state_manager import StateManager


class AnalysisProgressPage:
    """분석 진행 페이지"""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def render_analysis_page(self):
        """분석 진행 페이지 렌더링"""
        
        show_header("🔍 AI가 제품을 분석하고 있습니다...")
        
        # 세션 ID 확인
        session_id = StateManager.get_session_id()
        if not session_id:
            show_error_message("세션 정보가 없습니다. 메인 페이지로 돌아가서 다시 시작해 주세요.")
            st.write(f"현재 세션 ID: {session_id}")
            if st.button("🏠 메인 페이지로 이동"):
                StateManager.set_page("main")
                st.rerun()
            return
        
        # 분석 상태 확인
        self._check_and_display_analysis_status(session_id)
    
    def _check_and_display_analysis_status(self, session_id: str):
        """분석 상태 확인 및 표시"""
        
        # 분석 상태 조회
        status_result = self.api_client.get_product_status(session_id)
        
        if not status_result["success"]:
            error_msg = handle_api_error(status_result, "분석 상태를 확인할 수 없습니다.")
            show_error_message(error_msg)
            self._render_error_actions()
            return
        
        status_data = status_result["data"]["data"]
        current_status = status_data.get("status", "unknown")
        
        if current_status == "completed":
            # 분석 완료 - 결과 페이지로 이동
            self._handle_analysis_completion(session_id)
        elif current_status == "analyzing":
            # 분석 진행 중
            self._render_analysis_progress(session_id)
        elif current_status == "waiting":
            # 이미지 업로드 대기 중
            show_error_message("업로드된 이미지가 없습니다.")
            self._render_error_actions()
        else:
            # 알 수 없는 상태
            show_error_message(f"알 수 없는 분석 상태입니다: {current_status}")
            self._render_error_actions()
    
    def _render_analysis_progress(self, session_id: str):
        """분석 진행 상태 표시"""
        
        # 진행률 바와 상태 메시지
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            # 애니메이션 효과를 위한 진행률 바
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 단계별 진행 상태 표시
            steps = [
                {"text": "이미지 업로드 완료", "progress": 20},
                {"text": "AI 모델 로딩 중...", "progress": 40},
                {"text": "제품 인식 중...", "progress": 60},
                {"text": "브랜드 및 모델 분석 중...", "progress": 80},
                {"text": "사용법 정보 수집 중...", "progress": 95},
                {"text": "분석 완료!", "progress": 100}
            ]
            
            # 진행 상태 애니메이션
            for step in steps:
                progress_bar.progress(step["progress"])
                status_text.text(step["text"])
                time.sleep(0.8)  # 각 단계마다 0.8초 대기
        
        with status_container:
            st.info("📋 분석이 완료되면 자동으로 결과 페이지로 이동합니다.")
            
            # 예상 시간 안내
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("예상 소요 시간", "30-60초")
            with col2:
                st.metric("현재 단계", "AI 분석")
            with col3:
                st.metric("진행률", "분석 중...")
        
        # 실제 분석 완료 확인 (백그라운드)
        self._wait_for_completion(session_id)
    
    def _wait_for_completion(self, session_id: str):
        """분석 완료 대기"""
        
        # 자동 새로고침을 위한 placeholder
        auto_refresh = st.empty()
        
        with auto_refresh:
            # 3초 후 자동 새로고침
            time.sleep(3)
            
            # 분석 결과 확인
            result = self.api_client.get_analysis_result(session_id)
            
            if result["success"] and "product_info" in result["data"].get("data", {}):
                # 분석 완료
                show_success_message("✅ 제품 분석이 완료되었습니다!")
                time.sleep(1)
                StateManager.set_page("result")
                st.rerun()
            else:
                # 아직 진행 중이면 페이지 새로고침
                st.rerun()
    
    def _handle_analysis_completion(self, session_id: str):
        """분석 완료 처리"""
        
        # 결과 미리보기
        result = self.api_client.get_analysis_result(session_id)
        
        if result["success"]:
            data = result["data"]["data"]
            product_info = data.get("product_info", {})
            
            # 가전제품이 아닌 경우 처리
            if product_info.get("category") == "가전제품_아님":
                st.error("⚠️ 가전제품이 아닙니다")
                st.markdown("업로드하신 이미지는 가전제품이 아닙니다. 가전제품 사진을 촬영하여 다시 업로드해 주세요.")
                
                # 메인 페이지로 이동 버튼
                if st.button("🏠 메인 페이지로 이동", use_container_width=True):
                    StateManager.clear_state()
                    StateManager.set_page("main")
                    st.rerun()
                return
            
            # 가전제품인 경우 정상 처리
            show_success_message("🎉 제품 분석이 완료되었습니다!")
            
            st.markdown("### 📱 인식된 제품")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("브랜드", product_info.get("brand", "알 수 없음"))
            with col2:
                st.metric("제품", product_info.get("category", "가전제품"))
            with col3:
                st.metric("정확도", f"{product_info.get('confidence', 0):.1%}")
        
        # 결과 페이지로 이동 버튼
        if st.button("📋 상세 결과 보기", use_container_width=True):
            StateManager.set_page("result")
            st.rerun()
        
        # 자동 이동 (3초 후)
        with st.spinner("3초 후 자동으로 결과 페이지로 이동합니다..."):
            time.sleep(3)
            StateManager.set_page("result")
            st.rerun()
    
    def _render_error_actions(self):
        """오류 발생 시 액션 버튼들"""
        
        st.markdown("---")
        st.markdown("### 🔧 다음 중 하나를 선택해 주세요:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 메인 페이지로 이동", use_container_width=True):
                StateManager.clear_state()
                StateManager.set_page("main")
                st.rerun()
        
        with col2:
            if st.button("🔄 페이지 새로고침", use_container_width=True):
                st.rerun()
        
        with col3:
            if st.button("📞 도움말", use_container_width=True):
                self._show_help_info()
    
    def _show_help_info(self):
        """도움말 정보 표시"""
        
        with st.expander("📋 문제 해결 가이드", expanded=True):
            st.markdown("""
            **분석이 진행되지 않는 경우:**
            1. 네트워크 연결 상태를 확인해 주세요
            2. 브라우저를 새로고침해 주세요
            3. 이미지가 올바르게 업로드되었는지 확인해 주세요
            
            **지원되는 이미지:**
            - JPG, PNG, WEBP 형식
            - 최대 10MB 크기
            - 가전제품이 선명하게 보이는 이미지
            
            **문제가 계속되는 경우:**
            - 메인 페이지로 돌아가서 다시 시도해 주세요
            - 다른 이미지로 시도해 보세요
            """)
    
    def render_analysis_tips(self):
        """분석 중 팁 표시"""
        
        st.markdown("---")
        st.markdown("### 💡 분석 중이니 잠깐 팁을 확인해 보세요!")
        
        tips = [
            "🔍 AI가 제품의 브랜드, 모델, 특징을 자동으로 인식합니다",
            "📚 인식된 제품에 맞는 맞춤형 사용법을 제공합니다",
            "💬 분석 후 궁금한 점은 채팅으로 언제든 물어보세요",
            "🔄 결과가 정확하지 않다면 재분석을 요청할 수 있습니다",
            "📱 모바일에서도 동일하게 이용할 수 있습니다"
        ]
        
        for i, tip in enumerate(tips):
            time.sleep(0.5)  # 순차적으로 표시
            st.info(tip)


def render_analysis_page():
    """분석 페이지 렌더링 (메인 함수)"""
    
    analysis_page = AnalysisProgressPage()
    
    # 메인 분석 진행 화면
    analysis_page.render_analysis_page()
    
    # 구분선
    st.markdown("---")
    
    # 분석 팁 (비동기로 표시)
    if st.session_state.get("show_tips", True):
        analysis_page.render_analysis_tips()
        st.session_state.show_tips = False  # 한 번만 표시 