"""
결과 페이지 - 제품 분석 결과 표시
"""

import streamlit as st
from typing import Dict, Any
from services.api_client import get_api_client, handle_api_error
from services.state_manager import StateManager
from utils.ui_utils import show_success_message, show_error_message


class ProductResultPage:
    """제품 결과 페이지"""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def render_result_page(self):
        """결과 페이지 렌더링"""
        
        # 헤더
        st.header("📋 제품 분석 결과")
        
        # 세션 ID 확인
        session_id = StateManager.get_session_id()
        if not session_id:
            show_error_message("세션 정보가 없습니다. 메인 페이지로 돌아가서 다시 시작해 주세요.")
            self._render_navigation_buttons()
            return
        
        # 분석 결과 조회 및 표시
        self._load_and_display_results(session_id)
    
    def _load_and_display_results(self, session_id: str):
        """분석 결과 로드 및 표시"""
        
        with st.spinner("분석 결과를 불러오는 중..."):
            result = self.api_client.get_analysis_result(session_id)

        if not result["success"]:
            error_msg = handle_api_error(result, "분석 결과를 불러올 수 없습니다.")
            show_error_message(error_msg)
            self._render_navigation_buttons()
            return

        # 백엔드 응답 구조에 맞춰 데이터 추출
        data = result.get("data", {}).get("data", {})
        product_info = data.get("product_info", {})
        usage_guide = data.get("usage_guide", "")

        # ✅ product_info가 유효한 경우에만 상태 업데이트
        if product_info:
            StateManager.set_product_info(product_info)
        else:
            show_error_message("❌ 제품 분석 정보가 비어 있습니다.")
            self._render_navigation_buttons()
            return

        # ✅ 가전제품이 아닌 경우 처리
        if product_info.get("category") == "가전제품_아님":
            self._render_non_appliance_message(product_info)
            self._render_navigation_buttons()
            return

        # 성공 메시지
        show_success_message("✅ 제품 인식이 완료되었습니다!")

        # 제품 정보 표시
        self._render_product_info(product_info)

        # 사용법 가이드 표시
        if usage_guide:
            self._render_usage_guide(usage_guide)

        # 액션 버튼들
        self._render_action_buttons(session_id)

    
    def _render_product_info(self, product_info: Dict[str, Any]):
        """제품 정보 표시"""
        
        st.markdown("### 📱 인식된 제품 정보")
        
        # 메인 정보 카드
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="브랜드",
                    value=product_info.get("brand", "알 수 없음")
                )
            
            with col2:
                st.metric(
                    label="제품 종류",
                    value=product_info.get("category", "가전제품")
                )
            
            with col3:
                st.metric(
                    label="모델명",
                    value=product_info.get("model", "모델 미상")
                )
            
            with col4:
                confidence = product_info.get("confidence", 0)
                st.metric(
                    label="인식 정확도",
                    value=f"{confidence:.1%}",
                    delta=f"신뢰도: {'높음' if confidence > 0.8 else '보통' if confidence > 0.6 else '낮음'}"
                )
        
        # 제품 설명
        description = product_info.get("description", "")
        if description:
            st.markdown("### 📝 제품 설명")
            st.info(description)
        
        # 제품 특징
        features = product_info.get("features", [])
        if features:
            st.markdown("### ✨ 제품 특징")
            for feature in features:
                st.markdown(f"• {feature}")
    
    def _render_usage_guide(self, usage_guide: str):
        """사용법 가이드 표시"""
        
        st.markdown("### 📖 사용법 가이드")
        
        # 사용법 가이드를 마크다운으로 표시
        st.markdown(usage_guide)
        
        # 사용법 가이드 다운로드 버튼
        if st.button("📥 사용법 가이드 다운로드", use_container_width=True):
            st.download_button(
                label="📄 PDF로 다운로드",
                data=usage_guide,
                file_name="사용법_가이드.txt",
                mime="text/plain"
            )
    
    def _render_action_buttons(self, session_id: str):
        """액션 버튼들"""
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💬 더 자세한 사용법 문의하기", use_container_width=True):
                StateManager.set_page("chat")
                st.rerun()
        
        with col2:
            if st.button("🔄 재분석 요청", use_container_width=True):
                self._request_reanalysis(session_id)
        
        with col3:
            if st.button("🏠 다른 제품 분석하기", use_container_width=True):
                StateManager.clear_state()
                StateManager.set_page("main")
                st.rerun()
        
        # 추천 질문 표시
        self._render_suggested_questions(session_id)
    
    def _request_reanalysis(self, session_id: str):
        """재분석 요청"""
        
        with st.spinner("재분석을 요청하고 있습니다..."):
            result = self.api_client.reanalyze_product(session_id)
            
            if result["success"]:
                show_success_message("🔄 재분석이 시작되었습니다. 잠시 후 결과를 확인해 주세요.")
                st.rerun()
            else:
                error_msg = handle_api_error(result, "재분석 요청에 실패했습니다.")
                show_error_message(error_msg)
    
    def _render_suggested_questions(self, session_id: str):
        """추천 질문 표시"""
        
        st.markdown("### 💡 자주 묻는 질문")
        
        suggested_questions = [
            "이 제품의 기본 사용법을 알려주세요",
            "제품의 주요 기능은 무엇인가요?",
            "사용 시 주의사항이 있나요?",
            "청소 방법을 알려주세요",
            "고장 시 대처 방법은?"
        ]
        
        for question in suggested_questions:
            if st.button(f"❓ {question}", key=f"suggest_{question}"):
                # 채팅 페이지로 이동하고 질문 설정
                StateManager.set_page("chat")
                StateManager.set_suggested_question(question)
                st.rerun()
    
    def _render_non_appliance_message(self, product_info: Dict[str, Any]):
        """가전제품이 아닌 경우 메시지 표시"""
        
        st.markdown("### ⚠️ 가전제품이 아닙니다")
        
        # 백엔드에서 제공하는 메시지 표시
        message = product_info.get("message", "업로드하신 이미지는 가전제품이 아닙니다.")
        st.error(f"**{message}**")
        
        # 신뢰도 정보 표시
        confidence = product_info.get("confidence", 0)
        st.info(f"**판별 신뢰도:** {confidence:.1%}")
        
        # 안내 메시지
        st.info("""
        **올바른 가전제품 사진 촬영 방법:**
        1. 제품의 브랜드 로고가 잘 보이도록 촬영
        2. 제품 전체가 프레임에 들어오도록 촬영
        3. 밝은 곳에서 선명하게 촬영
        4. 제품의 특징적인 부분(버튼, 디스플레이 등)이 보이도록 촬영
        """)
    
    def _render_navigation_buttons(self):
        """네비게이션 버튼들"""
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🏠 메인 페이지로 돌아가기", use_container_width=True):
                StateManager.clear_state()
                StateManager.set_page("main")
                st.rerun()
        
        with col2:
            if st.button("🔄 페이지 새로고침", use_container_width=True):
                st.rerun()


def render_result_page():
    """결과 페이지 렌더링 (외부 호출용)"""
    page = ProductResultPage()
    page.render_result_page() 