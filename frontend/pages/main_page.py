"""
메인 페이지
"""

import streamlit as st
from utils.ui_utils import show_header
from components.upload_component import render_image_upload_page
from services.state_manager import StateManager


def render_main_page():
    """메인 페이지 렌더링"""
    
    # 이미지 업로드 페이지 렌더링
    session_id = render_image_upload_page()
    
    # 업로드 완료 후 분석 페이지로 자동 이동
    if session_id and st.session_state.get("analysis_started", False):
        StateManager.set_page("analysis")
        st.rerun()
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; margin-top: 2rem;">
    5060 중장년층을 위한 AI 가전제품 사용법 안내 서비스
    </div>
    """, unsafe_allow_html=True) 