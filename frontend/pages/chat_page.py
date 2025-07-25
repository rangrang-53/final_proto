"""
채팅 인터페이스 페이지
"""

import streamlit as st
from typing import List, Dict, Any, Optional
import time

from utils.ui_utils import show_header, show_error_message, show_success_message
from services.api_client import get_api_client, handle_api_error
from services.state_manager import StateManager


class ChatInterfacePage:
    """채팅 인터페이스 페이지"""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def render_chat_page(self):
        """채팅 페이지 렌더링"""
        
        show_header("💬 AI와 대화하기")
        
        # 세션 ID 확인
        session_id = StateManager.get_session_id()
        if not session_id:
            show_error_message("세션 정보가 없습니다. 메인 페이지로 돌아가서 다시 시작해 주세요.")
            self._render_navigation_buttons()
            return
        
        # 추천 질문 처리
        suggested_question = StateManager.get_suggested_question()
        if suggested_question:
            # 추천 질문을 자동으로 입력하고 전송
            self._send_message(session_id, suggested_question)
            StateManager.clear_suggested_question()
        
        # 제품 정보 표시
        self._render_product_info_header(session_id)
        
        # 채팅 히스토리 표시
        self._render_chat_history(session_id)
        
        # 추천 질문 표시
        self._render_suggested_questions(session_id)
        
        # 메시지 입력 영역
        self._render_message_input(session_id)
        
        # 채팅 관리 버튼들
        self._render_chat_controls(session_id)
    
    def _check_chat_status(self, session_id: str):
        """채팅 상태 확인"""
        
        result = self.api_client.get_chat_status(session_id)
        
        if result["success"]:
            status_data = result["data"]["data"]
            status = status_data.get("status", "unknown")
            
            if status == "waiting":
                st.warning("⚠️ 제품 분석을 먼저 완료해 주세요.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🏠 메인 페이지로 이동", use_container_width=True):
                        StateManager.set_page("main")
                        st.rerun()
                with col2:
                    if st.button("📋 결과 페이지로 이동", use_container_width=True):
                        StateManager.set_page("result")
                        st.rerun()
                return False
            
            elif status == "ready":
                st.info("💡 제품 분석이 완료되었습니다. 궁금한 점을 자유롭게 물어보세요!")
            
            elif status == "active":
                # 정상 상태 - 별도 메시지 없음
                pass
        
        return True
    
    def _render_product_info_header(self, session_id: str):
        """제품 정보 헤더"""
        
        # 분석 결과에서 제품 정보 가져오기
        result = self.api_client.get_analysis_result(session_id)
        
        if result["success"]:
            data = result["data"]["data"]
            product_info = data.get("product_info", {})
            
            if product_info:
                brand = product_info.get("brand", "알 수 없음")
                category = product_info.get("category", "가전제품")
                model = product_info.get("model", "모델 미상")
                
                st.info(f"📱 현재 상담 제품: **{brand} {category} {model}**")
            else:
                st.warning("제품 정보를 불러올 수 없습니다.")
    
    def _render_chat_history(self, session_id: str):
        """채팅 히스토리 표시"""
        
        # 채팅 히스토리 조회
        result = self.api_client.get_chat_history(session_id, limit=50)
        
        if not result["success"]:
            st.error("채팅 히스토리를 불러올 수 없습니다.")
            return
        
        chat_data = result["data"]["data"]
        messages = chat_data.get("messages", [])
        
        if not messages:
            # 첫 대화인 경우 환영 메시지
            st.chat_message("assistant").write(
                "안녕하세요! 가전제품 사용법 안내 AI입니다. 😊\n\n"
                "제품에 대해 궁금한 점이 있으시면 언제든 물어보세요!\n"
                "아래 추천 질문을 참고하시거나 직접 질문을 입력해 주세요."
            )
        else:
            # 기존 채팅 히스토리 표시
            for message in messages:
                role = message["role"]
                content = message["message"]
                
                with st.chat_message(role):
                    st.write(content)
    
    def _render_suggested_questions(self, session_id: str):
        """추천 질문 표시"""
        
        # 채팅 히스토리가 없는 경우에만 추천 질문 표시
        history_result = self.api_client.get_chat_history(session_id, limit=1)
        
        if history_result["success"]:
            messages = history_result["data"]["data"].get("messages", [])
            
            if len(messages) == 0:  # 첫 대화인 경우
                st.markdown("### 💡 추천 질문")
                
                # 추천 질문 조회
                suggestions_result = self.api_client.get_suggested_questions(session_id)
                
                if suggestions_result["success"]:
                    suggestions = suggestions_result["data"]["data"]["suggestions"]
                    
                    # 추천 질문을 버튼으로 표시 (2열로)
                    cols = st.columns(2)
                    for i, question in enumerate(suggestions[:6]):
                        with cols[i % 2]:
                            if st.button(f"❓ {question}", key=f"suggestion_{i}", use_container_width=True):
                                self._send_message(session_id, question)
                                st.rerun()
    
    def _render_message_input(self, session_id: str):
        """메시지 입력 영역"""
        
        # 채팅 입력
        if prompt := st.chat_input("궁금한 점을 입력해 주세요..."):
            self._send_message(session_id, prompt)
    
    def _send_message(self, session_id: str, message: str):
        """메시지 전송"""
        
        # 중복 전송 방지
        if "last_sent_message" in st.session_state and st.session_state.last_sent_message == message:
            return
        
        # 마지막 전송 메시지 저장
        st.session_state.last_sent_message = message
        
        # 사용자 메시지 즉시 표시
        with st.chat_message("user"):
            st.write(message)
        
        # AI 응답 요청
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하고 있습니다..."):
                result = self.api_client.send_chat_message(session_id, message)
                
                if result["success"]:
                    data = result["data"]["data"]
                    ai_response = data["ai_response"]["message"]
                    st.write(ai_response)
                    
                    # 상태 업데이트
                    st.session_state.last_message_time = time.time()
                    
                else:
                    error_msg = handle_api_error(result, "메시지 전송에 실패했습니다.")
                    st.error(error_msg)
        
        # 메시지 전송 완료 후 상태 초기화
        if "last_sent_message" in st.session_state:
            del st.session_state.last_sent_message
    
    def _render_chat_controls(self, session_id: str):
        """채팅 제어 버튼들"""
        
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🗑️ 채팅 초기화", use_container_width=True):
                self._clear_chat_history(session_id)
        
        with col2:
            if st.button("📊 채팅 통계", use_container_width=True):
                self._show_chat_statistics(session_id)
        
        with col3:
            if st.button("📋 결과 페이지", use_container_width=True):
                StateManager.set_page("result")
                st.rerun()
        
        with col4:
            if st.button("🔄 다른 제품 분석", use_container_width=True):
                StateManager.clear_state()
                StateManager.set_page("main")
                st.rerun()
    
    def _clear_chat_history(self, session_id: str):
        """채팅 히스토리 초기화"""
        
        if st.button("정말로 채팅 히스토리를 삭제하시겠습니까?", key="confirm_clear"):
            with st.spinner("채팅 히스토리를 초기화하고 있습니다..."):
                result = self.api_client.clear_chat_history(session_id)
                
                if result["success"]:
                    st.success("✅ 채팅 히스토리가 초기화되었습니다.")
                    time.sleep(1)
                    st.rerun()
                else:
                    error_msg = handle_api_error(result, "채팅 히스토리 초기화에 실패했습니다.")
                    st.error(error_msg)
    
    def _show_chat_statistics(self, session_id: str):
        """채팅 통계 표시"""
        
        result = self.api_client.get_chat_statistics(session_id)
        
        if result["success"]:
            stats = result["data"]["data"]
            
            with st.expander("📊 채팅 통계", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("전체 메시지", stats.get("total_messages", 0))
                
                with col2:
                    st.metric("내 질문", stats.get("user_messages", 0))
                
                with col3:
                    st.metric("AI 답변", stats.get("ai_messages", 0))
                
                # 시간 정보
                first_chat = stats.get("first_chat_at", "")
                last_chat = stats.get("last_chat_at", "")
                
                if first_chat:
                    st.text(f"첫 대화: {first_chat.replace('T', ' ')[:19]}")
                if last_chat:
                    st.text(f"마지막 대화: {last_chat.replace('T', ' ')[:19]}")
        else:
            st.error("통계 정보를 불러올 수 없습니다.")
    
    def _render_navigation_buttons(self):
        """네비게이션 버튼들"""
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 메인 페이지", use_container_width=True):
                StateManager.clear_state()
                StateManager.set_page("main")
                st.rerun()
        
        with col2:
            if st.button("📋 결과 페이지", use_container_width=True):
                StateManager.set_page("result")
                st.rerun()
        
        with col3:
            if st.button("🔄 새로고침", use_container_width=True):
                st.rerun()
    
    def render_chat_tips(self):
        """채팅 사용 팁"""
        
        with st.expander("💡 채팅 사용 팁"):
            st.markdown("""
            **효과적인 질문 방법:**
            - 구체적으로 질문해 주세요 (예: "온도를 어떻게 조절하나요?")
            - 단계별로 나누어 질문해 보세요
            - 문제 상황을 자세히 설명해 주세요
            
            **이런 질문을 할 수 있어요:**
            - 기본 사용법 및 조작 방법
            - 청소 및 관리 방법
            - 고장 진단 및 해결 방법
            - 안전 사용법 및 주의사항
            - 효율적인 활용 팁
            
            **주의사항:**
            - AI는 일반적인 가이드를 제공합니다
            - 안전과 관련된 문제는 전문가에게 문의하세요
            - 정확한 모델별 정보는 매뉴얼을 확인하세요
            """)


def render_chat_page():
    """채팅 페이지 렌더링 (메인 함수)"""
    
    chat_page = ChatInterfacePage()
    
    # 채팅 상태가 정상인 경우에만 채팅 인터페이스 표시
    if chat_page._check_chat_status(StateManager.get_session_id() or ""):
        # 메인 채팅 화면
        chat_page.render_chat_page()
        
        # 채팅 사용 팁
        chat_page.render_chat_tips() 