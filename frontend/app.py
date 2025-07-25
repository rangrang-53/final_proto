"""
Streamlit 메인 애플리케이션
"""

import streamlit as st
st.session_state["debug_mode"] = True
from utils.ui_utils import set_page_config, apply_custom_css
from utils.constants import PAGES
from services.state_manager import StateManager
from services.api_client import get_or_create_session, check_backend_connection
from pages.main_page import render_main_page
from pages.analysis_page import render_analysis_page
from pages.result_page import render_result_page
from pages.chat_page import render_chat_page
from pages.config_page import render_config_page


def main():
    """메인 함수"""
    
    # 페이지 설정
    set_page_config()
    
    # 커스텀 CSS 적용
    apply_custom_css()
    
    # 상태 초기화
    StateManager.initialize_state()
    
    # 백엔드 연결 확인 (세션 상태에 저장하여 중복 확인 방지)
    if "backend_connected" not in st.session_state:
        if not check_backend_connection():
            st.error("🔌 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요.")
            st.info("백엔드 서버를 실행한 후 페이지를 새로고침해 주세요.")
            return
        st.session_state.backend_connected = True
    
    # 세션 ID 확인/생성 (이미 있으면 재사용)
    if "session_id" not in st.session_state:
        session_id = get_or_create_session()
        if not session_id:
            st.error("세션을 생성할 수 없습니다. 페이지를 새로고침해 주세요.")
            return
    else:
        session_id = st.session_state.session_id
    
    # 현재 페이지 가져오기
    current_page = StateManager.get_current_page()
    if not current_page:
        StateManager.set_page("main")
        st.rerun()
        return
    
    # 페이지 라우팅
    if current_page == "main":
        render_main_page()
    elif current_page == "analysis":
        from pages.analysis_page import render_analysis_page
        render_analysis_page()
    elif current_page == "result":
        from pages.result_page import render_result_page
        render_result_page()
    elif current_page == "chat":
        from pages.chat_page import render_chat_page
        render_chat_page()
    else:
        st.error("존재하지 않는 페이지입니다.")


if __name__ == "__main__":
    main() 