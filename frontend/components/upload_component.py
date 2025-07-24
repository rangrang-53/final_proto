"""
이미지 업로드 컴포넌트
"""

import streamlit as st
from PIL import Image
from typing import Optional, Tuple
import io

from utils.ui_utils import (
    show_success_message, show_error_message, 
    validate_image_file, resize_image
)
from services.api_client import get_api_client, handle_api_error
from services.state_manager import StateManager


class ImageUploadComponent:
    """이미지 업로드 컴포넌트"""
    
    def __init__(self):
        self.api_client = get_api_client()
    
    def render_upload_area(self) -> Optional[str]:
        """이미지 업로드 영역 렌더링"""
        
        st.markdown("""
        <div class="upload-area">
            <h3>📱 가전제품 이미지를 업로드해 주세요</h3>
            <p>AI가 제품을 인식하고 사용법을 안내해 드립니다</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 업로드 방법 선택
        upload_method = st.radio(
            "업로드 방법을 선택하세요:",
            ["📁 파일 선택", "📷 카메라 촬영"],
            horizontal=True
        )
        
        uploaded_file = None
        
        if upload_method == "📁 파일 선택":
            uploaded_file = st.file_uploader(
                "이미지 파일을 선택하세요",
                type=['jpg', 'jpeg', 'png', 'webp'],
                help="JPG, PNG, WEBP 형식을 지원합니다 (최대 10MB)"
            )
        else:
            uploaded_file = st.camera_input("카메라로 촬영하기")
        
        if uploaded_file is not None:
            return self._process_uploaded_file(uploaded_file)
        
        return None
    
    def _process_uploaded_file(self, uploaded_file) -> Optional[str]:
        """업로드된 파일 처리"""
        
        # 파일 검증
        is_valid, message = validate_image_file(uploaded_file)
        
        if not is_valid:
            show_error_message(message)
            return None
        
        try:
            # 파일 포인터를 처음으로 이동
            uploaded_file.seek(0)
            
            # 이미지 표시
            image = Image.open(uploaded_file)
            resized_image = resize_image(image, 800)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(resized_image, caption="업로드된 이미지", use_container_width=True)
            
            # 세션 ID 확인
            if "session_id" not in st.session_state:
                show_error_message("세션이 생성되지 않았습니다. 페이지를 새로고침해 주세요.")
                return None
            
            # 파일 업로드 버튼
            if st.button("🔍 이미지 업로드 및 분석 시작", use_container_width=True):
                return self._upload_to_backend(uploaded_file)
            
            return None
            
        except Exception as e:
            show_error_message(f"이미지 처리 중 오류가 발생했습니다: {str(e)}")
            return None
    
    def _upload_to_backend(self, uploaded_file) -> Optional[str]:
        """백엔드로 파일 업로드"""
        
        with st.spinner("이미지를 업로드하고 있습니다..."):
            try:
                # 파일 포인터를 처음으로 이동
                uploaded_file.seek(0)
                
                # 파일 데이터 읽기
                file_data = uploaded_file.read()
                filename = uploaded_file.name
                
                # 파일이 비어있는지 확인
                if not file_data:
                    show_error_message("파일이 비어있습니다. 다시 업로드해 주세요.")
                    return None
                
                # 기존 세션 ID 가져오기 (StateManager 사용)
                existing_session_id = StateManager.get_session_id()
                
                # 백엔드로 업로드
                result = self.api_client.upload_image(file_data, filename, existing_session_id)
                
                if result["success"]:
                    data = result["data"]
                    session_id = data["data"]["session_id"]
                    
                    # 세션 ID 저장 (StateManager 사용)
                    StateManager.set_session_id(session_id)
                    
                    # 제품 인식 결과 확인
                    product_recognition = data["data"].get("product_recognition", {})
                    
                    # 가전제품이 아닌 경우 즉시 알림
                    if product_recognition.get("category") == "가전제품_아님":
                        # JavaScript alert 표시
                        st.markdown("""
                        <script>
                        alert("⚠️ 가전제품이 아닙니다!\\n\\n업로드하신 이미지는 가전제품이 아닙니다.\\n가전제품 사진을 촬영하여 다시 업로드해 주세요.");
                        </script>
                        """, unsafe_allow_html=True)
                        
                        st.error("⚠️ 가전제품이 아닙니다")
                        st.markdown(product_recognition.get("message", "업로드하신 이미지는 가전제품이 아닙니다. 가전제품 사진을 촬영하여 다시 업로드해 주세요."))
                        
                        # 메인 페이지로 이동 버튼
                        if st.button("🏠 다시 업로드하기", use_container_width=True):
                            st.rerun()
                        return None
                    
                    show_success_message("✅ 이미지가 성공적으로 업로드되었습니다!")
                    
                    # 자동으로 분석 시작
                    self._start_analysis(session_id)
                    
                    return session_id
                else:
                    error_msg = handle_api_error(result, "이미지 업로드에 실패했습니다.")
                    show_error_message(error_msg)
                    return None
                    
            except Exception as e:
                show_error_message(f"업로드 중 오류가 발생했습니다: {str(e)}")
                return None
    
    def _start_analysis(self, session_id: str):
        """제품 분석 시작"""
        
        with st.spinner("AI가 제품을 분석하고 있습니다..."):
            try:
                # 분석 시작 요청
                result = self.api_client.analyze_product(session_id)
                
                if result["success"]:
                    st.success("🔍 제품 분석이 시작되었습니다!")
                    st.info("분석이 완료되면 자동으로 결과 페이지로 이동합니다.")
                    
                    # 상태 업데이트
                    st.session_state.analysis_started = True
                    
                else:
                    error_msg = handle_api_error(result, "제품 분석 시작에 실패했습니다.")
                    show_error_message(error_msg)
                    
            except Exception as e:
                show_error_message(f"분석 시작 중 오류가 발생했습니다: {str(e)}")
    
    def check_upload_status(self, session_id: str) -> dict:
        """업로드 상태 확인"""
        
        try:
            result = self.api_client.get_upload_status(session_id)
            
            if result["success"]:
                return result["data"]["data"]
            else:
                return {"status": "error", "message": handle_api_error(result)}
                
        except Exception as e:
            return {"status": "error", "message": f"상태 확인 중 오류: {str(e)}"}
    
    def render_upload_progress(self, session_id: str):
        """업로드 진행 상태 표시"""
        
        status_data = self.check_upload_status(session_id)
        
        if status_data["status"] == "uploaded":
            st.success("✅ 이미지 업로드 완료")
            
            # 이미지 정보 표시
            if "image_info" in status_data:
                image_info = status_data["image_info"]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("파일 형식", image_info.get("format", "Unknown"))
                with col2:
                    st.metric("이미지 크기", f"{image_info.get('width', 0)}x{image_info.get('height', 0)}")
                with col3:
                    st.metric("업로드 시간", status_data.get("uploaded_at", "").split("T")[0])
        
        elif status_data["status"] == "no_image":
            st.warning("⚠️ 업로드된 이미지가 없습니다.")
            
        elif status_data["status"] == "error":
            st.error(f"❌ {status_data['message']}")
    
    def render_supported_formats(self):
        """지원 형식 안내"""
        
        with st.expander("📋 지원하는 이미지 형식"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **지원 형식:**
                - JPG, JPEG
                - PNG
                - WEBP
                """)
            
            with col2:
                st.markdown("""
                **권장 사항:**
                - 최대 파일 크기: 10MB
                - 최소 해상도: 100x100px
                - 제품이 선명하게 보이는 이미지
                """)
    
    def render_upload_tips(self):
        """업로드 팁 안내"""
        
        st.markdown("### 💡 더 정확한 인식을 위한 촬영 팁")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🎯 촬영 각도**
            - 제품 정면에서 촬영
            - 브랜드 로고가 잘 보이게
            - 기울어지지 않게 수평으로
            """)
        
        with col2:
            st.markdown("""
            **💡 조명**
            - 충분한 자연광 또는 조명
            - 그림자가 지지 않게
            - 반사광 피하기
            """)
        
        with col3:
            st.markdown("""
            **📐 구도**
            - 제품 전체가 화면에 들어오게
            - 배경은 단순하게
            - 다른 물건과 겹치지 않게
            """)


def render_image_upload_page():
    """이미지 업로드 페이지 렌더링"""
    
    upload_component = ImageUploadComponent()
    
    # 업로드 영역
    session_id = upload_component.render_upload_area()
    
    # 구분선
    st.markdown("---")
    
    # 업로드 팁
    upload_component.render_upload_tips()
    
    # 지원 형식 안내
    upload_component.render_supported_formats()
    
    return session_id 