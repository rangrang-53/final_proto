"""
프론트엔드 상수 정의
"""

# API 엔드포인트
BACKEND_BASE_URL = "http://localhost:8000"
API_ENDPOINTS = {
    "health": f"{BACKEND_BASE_URL}/api/health",
    "analyze_product": f"{BACKEND_BASE_URL}/api/analyze-product",
    "chat": f"{BACKEND_BASE_URL}/api/chat",
    "session_create": f"{BACKEND_BASE_URL}/api/session/create",
    "session_get": f"{BACKEND_BASE_URL}/api/session",
    "session_delete": f"{BACKEND_BASE_URL}/api/session"
}

# 페이지 설정
PAGES = {
    "main": "📱 메인",
    "analysis": "🔍 분석중",
    "result": "📋 결과",
    "chat": "💬 채팅"
}

# UI 설정
UI_CONFIG = {
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": ["jpg", "jpeg", "png", "webp"],
    "image_max_width": 800,
    "chat_max_messages": 50
}

# 메시지
MESSAGES = {
    "upload_success": "✅ 이미지가 성공적으로 업로드되었습니다!",
    "upload_error": "❌ 이미지 업로드 중 오류가 발생했습니다.",
    "analysis_start": "🔍 AI가 제품을 분석중입니다...",
    "analysis_complete": "✅ 분석이 완료되었습니다!",
    "analysis_error": "❌ 분석 중 오류가 발생했습니다.",
    "chat_error": "❌ 메시지 전송 중 오류가 발생했습니다."
} 