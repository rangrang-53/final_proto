"""
UI 헬퍼 함수
"""

import streamlit as st
from typing import Optional
from PIL import Image
import io


def set_page_config():
    """페이지 설정"""
    st.set_page_config(
        page_title="가전제품 사용법 안내",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="collapsed"
    )


def apply_custom_css():
    """커스텀 CSS 적용"""
    st.markdown("""
    <style>
    /* 중장년층 친화적 스타일 */
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        color: #2E4057;
        margin-bottom: 2rem;
    }
    
    .upload-area {
        border: 3px dashed #007bff;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .info-message {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* 큰 버튼 스타일 */
    .stButton > button {
        height: 4rem;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 10px;
    }
    
    /* 텍스트 크기 조정 */
    .big-text {
        font-size: 1.3rem;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)


def show_header(title: str):
    """헤더 표시"""
    st.markdown(f'<h1 class="main-header">{title}</h1>', unsafe_allow_html=True)


def show_success_message(message: str):
    """성공 메시지 표시"""
    st.markdown(f'<div class="success-message">{message}</div>', unsafe_allow_html=True)


def show_error_message(message: str):
    """에러 메시지 표시"""
    st.markdown(f'<div class="error-message">{message}</div>', unsafe_allow_html=True)


def show_info_message(message: str):
    """정보 메시지 표시"""
    st.markdown(f'<div class="info-message">{message}</div>', unsafe_allow_html=True)


def validate_image_file(uploaded_file) -> tuple[bool, str]:
    """이미지 파일 검증"""
    if uploaded_file is None:
        return False, "파일이 선택되지 않았습니다."
    
    # 파일 크기 검증
    if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
        return False, "파일 크기가 10MB를 초과합니다."
    
    # 파일 확장자 검증
    allowed_extensions = ["jpg", "jpeg", "png", "webp"]
    file_extension = uploaded_file.name.split(".")[-1].lower()
    if file_extension not in allowed_extensions:
        return False, f"지원하지 않는 파일 형식입니다. ({', '.join(allowed_extensions)}만 지원)"
    
    return True, "유효한 파일입니다."


def resize_image(image: Image.Image, max_width: int = 800) -> Image.Image:
    """이미지 크기 조정"""
    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        return image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    return image


def create_progress_bar(progress: int, message: str = ""):
    """진행률 바 생성"""
    progress_bar = st.progress(progress / 100)
    if message:
        st.text(message)
    return progress_bar 