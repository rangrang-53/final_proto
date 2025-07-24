# 5060 중장년층 가전제품 사용법 안내 Agent

## 프로젝트 개요
5060 중장년층이 가전제품 설명서의 작은 글씨로 인해 겪는 불편함을 해결하기 위한 AI 기반 웹 서비스 프로토타입입니다.

## 주요 기능
- 📷 **이미지 기반 제품 인식**: 가전제품을 촬영하면 AI가 브랜드와 모델을 자동 인식
- 🤖 **AI Agent 대화**: LangGraph 기반 대화형 사용법 안내
- 📖 **시각적 가이드**: 중장년층 친화적인 단계별 사용법 제공
- 🔍 **실시간 검색**: Naver/Exa Search를 통한 최신 사용법 정보 수집

## 기술 스택
- **Backend**: FastAPI + Python 3.11
- **Frontend**: Streamlit
- **AI**: LangGraph + Gemini-2.5-flash-preview-05-20
- **Tools**: Naver Search MCP, Exa Search MCP

## 설치 및 실행

### 1. 환경 설정
```bash
# 환경 변수 설정
cp env.example .env
# .env 파일을 열어서 API 키 설정
```

### 2. 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 프론트엔드 실행
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

## 프로젝트 구조
```
proto/
├── backend/          # FastAPI 백엔드
├── frontend/         # Streamlit 프론트엔드
├── shared/           # 공통 모듈
├── tests/            # 테스트 코드
└── docs/             # 문서
```

## 개발 진행 상황
- ✅ T001: 프로젝트 초기 설정
- 🔄 T002: FastAPI 백엔드 기본 구조 (진행 예정)
- ⏳ T003~T016: 기타 개발 태스크들

## 라이선스
MIT License 