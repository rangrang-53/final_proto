"""
상태 관리 서비스
"""

import streamlit as st
from typing import Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AppState:
    """애플리케이션 상태"""
    current_page: str = "main"
    session_id: Optional[str] = None
    uploaded_image: Optional[Any] = None
    product_info: Optional[Dict] = None
    chat_history: list = None
    suggested_question: Optional[str] = None
    
    def __post_init__(self):
        if self.chat_history is None:
            self.chat_history = []


class StateManager:
    """상태 관리자"""
    
    @staticmethod
    def initialize_state():
        """상태 초기화"""
        if "app_state" not in st.session_state:
            st.session_state.app_state = AppState()
    
    @staticmethod
    def get_state() -> AppState:
        """현재 상태 조회"""
        StateManager.initialize_state()
        return st.session_state.app_state
    
    @staticmethod
    def set_page(page: str):
        """페이지 변경"""
        state = StateManager.get_state()
        state.current_page = page
        st.session_state.app_state = state
    
    @staticmethod
    def set_session_id(session_id: str):
        """세션 ID 설정"""
        state = StateManager.get_state()
        state.session_id = session_id
        st.session_state.app_state = state
    
    @staticmethod
    def set_uploaded_image(image):
        """업로드된 이미지 설정"""
        state = StateManager.get_state()
        state.uploaded_image = image
        st.session_state.app_state = state
    
    @staticmethod
    def set_product_info(product_info: Dict):
        """제품 정보 설정"""
        state = StateManager.get_state()
        state.product_info = product_info
        st.session_state.app_state = state
    
    @staticmethod
    def add_chat_message(role: str, message: str):
        """채팅 메시지 추가"""
        state = StateManager.get_state()
        state.chat_history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        st.session_state.app_state = state
    
    @staticmethod
    def clear_state():
        """상태 초기화"""
        st.session_state.app_state = AppState()
    
    @staticmethod
    def get_session_id() -> Optional[str]:
        """세션 ID 조회"""
        return StateManager.get_state().session_id
    
    @staticmethod
    def get_current_page() -> str:
        """현재 페이지 조회"""
        return StateManager.get_state().current_page
    
    @staticmethod
    def get_uploaded_image():
        """업로드된 이미지 조회"""
        return StateManager.get_state().uploaded_image
    
    @staticmethod
    def get_product_info() -> Optional[Dict]:
        """제품 정보 조회"""
        return StateManager.get_state().product_info
    
    @staticmethod
    def get_chat_history() -> list:
        """채팅 히스토리 조회"""
        return StateManager.get_state().chat_history
    
    @staticmethod
    def set_suggested_question(question: str):
        """추천 질문 설정"""
        state = StateManager.get_state()
        state.suggested_question = question
        st.session_state.app_state = state
    
    @staticmethod
    def get_suggested_question() -> Optional[str]:
        """추천 질문 조회"""
        return StateManager.get_state().suggested_question
    
    @staticmethod
    def clear_suggested_question():
        """추천 질문 초기화"""
        state = StateManager.get_state()
        state.suggested_question = None
        st.session_state.app_state = state 