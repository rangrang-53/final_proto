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

## 사용한 AI 모델

### 🤖 핵심 AI 모델
- **Google Gemini 2.5 Flash Preview**: 
  - 제품 이미지 분석 및 인식
  - 자연어 대화 및 사용법 가이드 생성
  - 실시간 제품 정보 추출

### 🔍 컴퓨터 비전 & OCR
- **EasyOCR**: 
  - 이미지에서 텍스트 추출 (한국어/영어)
  - 브랜드명, 모델명, 제품 정보 인식
  - 신뢰도 기반 텍스트 필터링

### 🧠 AI 프레임워크
- **LangGraph**: 
  - 대화형 AI Agent 구축
  - 복잡한 워크플로우 관리
  - 도구 사용 및 메모리 관리

- **LangChain**: 
  - AI 모델 통합 및 프롬프트 관리
  - 검색 도구 연동
  - 메모리 및 세션 관리

### 🔧 검색 및 도구
- **네이버 검색 API**:
  - 이미지 검색: 유사한 제품 이미지 찾기
  - 웹 검색: 최신 제품 정보 수집
  - 쇼핑 검색: 제품 가격 및 상세 정보

- **Exa Search API**:
  - 실시간 웹 검색
  - 학술 자료 및 전문 정보 수집

### 📊 데이터 처리
- **OpenCV**: 이미지 전처리 및 분석
- **Pillow (PIL)**: 이미지 처리 및 변환
- **NumPy**: 수치 계산 및 배열 처리
- **Pandas**: 데이터 분석 및 처리

### 🌐 웹 기술
- **FastAPI**: 고성능 백엔드 API
- **Streamlit**: 대화형 웹 인터페이스
- **Uvicorn**: ASGI 서버
- **aiohttp**: 비동기 HTTP 클라이언트

### 🗄️ 데이터베이스 & 메모리
- **Memory Database**: 세션 및 임시 데이터 저장
- **LangSmith**: AI 모델 성능 모니터링
- **Python-dotenv**: 환경 변수 관리

## 설치 및 실행

### 1. 환경 설정

#### API 키 발급
1. **Google API 키**: [Google Cloud Console](https://console.cloud.google.com/)에서 Gemini API 키 발급
2. **네이버 API 키**: [네이버 개발자 센터](https://developers.naver.com/)에서 애플리케이션 등록 후 클라이언트 ID와 시크릿 발급

#### 환경 변수 설정
```bash
# 환경 변수 설정
cp env.example .env
# .env 파일을 열어서 API 키 설정
```

`.env` 파일 예시:
```env
# API 키 설정
GOOGLE_API_KEY=your_google_api_key_here
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here

# 서버 설정
BACKEND_HOST=localhost
BACKEND_PORT=8000
FRONTEND_HOST=localhost
FRONTEND_PORT=8501
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
proto_jr/
├── backend/                    # FastAPI 백엔드
│   ├── api/                   # API 라우터
│   │   ├── routes/           # 엔드포인트 정의
│   │   └── dependencies.py   # 의존성 주입
│   ├── core/                 # 핵심 AI 로직
│   │   ├── agent/           # LangGraph Agent
│   │   │   ├── agent_core.py # 메인 Agent 클래스
│   │   │   ├── prompts/     # 시스템 프롬프트
│   │   │   └── tools/       # 검색 도구들
│   │   └── memory/          # 메모리 관리
│   ├── services/            # 비즈니스 로직
│   │   ├── product_recognition_service.py # 제품 인식
│   │   ├── simple_product_search_service.py # 제품 검색
│   │   └── chat_service.py  # 대화 서비스
│   ├── config/              # 설정 관리
│   ├── models/              # 데이터 모델
│   ├── utils/               # 유틸리티
│   └── main.py              # 애플리케이션 진입점
├── frontend/                 # Streamlit 프론트엔드
│   ├── pages/               # 페이지 컴포넌트
│   ├── components/          # UI 컴포넌트
│   ├── services/            # API 클라이언트
│   └── app.py               # 메인 앱
├── shared/                   # 공통 모듈
├── tests/                    # 테스트 코드
├── docs/                     # 문서 및 UX 와이어프레임
└── requirements.txt          # 의존성 목록
```

## 주요 기능 상세

### 📷 이미지 기반 제품 인식
- **OCR 텍스트 추출**: EasyOCR을 사용한 브랜드명, 모델명 인식
- **AI 이미지 분석**: Gemini 2.5 Flash로 제품 카테고리 분류
- **이미지 검색**: 네이버 이미지 검색 API로 유사 제품 찾기
- **신뢰도 평가**: 확신도 기반 결과 필터링

### 🤖 AI Agent 대화 시스템
- **LangGraph 기반 워크플로우**: 복잡한 대화 흐름 관리
- **도구 사용**: 검색, 이미지 분석 등 다양한 도구 활용
- **메모리 관리**: 세션별 대화 기록 및 컨텍스트 유지
- **자연어 처리**: 한국어 기반 자연스러운 대화

### 🔍 실시간 검색 시스템
- **네이버 검색 API**: 이미지, 웹, 쇼핑 검색 통합
- **Exa Search**: 실시간 웹 검색 및 학술 자료 수집
- **검색 결과 분석**: AI 기반 검색 결과 요약 및 정리
- **캐싱 시스템**: 검색 결과 효율적 관리

### 📖 사용법 가이드 생성
- **단계별 가이드**: 중장년층 친화적인 설명
- **시각적 요소**: 이미지와 함께 제공되는 가이드
- **안전 정보**: 제품별 안전 주의사항 포함
- **트러블슈팅**: 일반적인 문제 해결 방법 제공

## 시스템 프로세스 다이어그램

### 🔄 전체 시스템 흐름
```mermaid
graph TD
    A[사용자 이미지 업로드] --> B[이미지 전처리]
    B --> C[OCR 텍스트 추출]
    C --> D[AI 이미지 분석]
    D --> E[제품 인식 결과]
    
    E --> F{가전제품인가?}
    F -->|아니오| G[가전제품 아님 메시지]
    F -->|예| H[이미지 기반 검색]
    
    H --> I[네이버 이미지 검색]
    I --> J[제품 정보 추출]
    J --> K[AI Agent 대화 시작]
    
    K --> L[사용법 가이드 생성]
    L --> M[실시간 검색]
    M --> N[최종 결과 제공]
    
    G --> O[결과 페이지 표시]
    N --> O
    
    style A fill:#e1f5fe
    style E fill:#f3e5f5
    style K fill:#e8f5e8
    style O fill:#fff3e0
```

### 🤖 AI Agent 워크플로우
```mermaid
graph LR
    A[사용자 질문] --> B[LangGraph Agent]
    B --> C{도구 사용 필요?}
    C -->|예| D[검색 도구 실행]
    C -->|아니오| E[AI 응답 생성]
    
    D --> F[네이버 검색]
    D --> G[Exa 검색]
    D --> H[이미지 검색]
    
    F --> I[검색 결과 분석]
    G --> I
    H --> I
    
    I --> J[AI 응답 생성]
    E --> K[사용자에게 응답]
    J --> K
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style K fill:#e8f5e8
```

### 📷 제품 인식 프로세스
```mermaid
graph TD
    A[이미지 업로드] --> B[EasyOCR 텍스트 추출]
    B --> C[브랜드명/모델명 인식]
    C --> D[Gemini AI 이미지 분석]
    
    D --> E[제품 카테고리 분류]
    E --> F[신뢰도 평가]
    
    F --> G{신뢰도 > 0.7?}
    G -->|예| H[이미지 기반 검색]
    G -->|아니오| I[기본 분류 결과]
    
    H --> J[네이버 이미지 검색 API]
    J --> K[유사 제품 찾기]
    K --> L[제품 정보 추출]
    
    I --> M[최종 제품 정보]
    L --> M
    
    style A fill:#e1f5fe
    style D fill:#f3e5f5
    style M fill:#e8f5e8
```

### 🔍 검색 시스템 아키텍처
```mermaid
graph TB
    A[검색 요청] --> B{검색 유형}
    
    B -->|이미지 검색| C[네이버 이미지 API]
    B -->|웹 검색| D[네이버 웹 API]
    B -->|쇼핑 검색| E[네이버 쇼핑 API]
    B -->|실시간 검색| F[Exa Search API]
    
    C --> G[이미지 결과]
    D --> H[웹 문서 결과]
    E --> I[제품 정보 결과]
    F --> J[실시간 웹 결과]
    
    G --> K[결과 분석]
    H --> K
    I --> K
    J --> K
    
    K --> L[AI 요약 및 정리]
    L --> M[사용자에게 제공]
    
    style A fill:#e1f5fe
    style K fill:#f3e5f5
    style M fill:#e8f5e8
```

### 🏗️ 시스템 아키텍처
```mermaid
graph TB
    subgraph "Frontend (Streamlit)"
        A[사용자 인터페이스]
        B[이미지 업로드]
        C[대화 인터페이스]
    end
    
    subgraph "Backend (FastAPI)"
        D[API Gateway]
        E[세션 관리]
        F[파일 처리]
    end
    
    subgraph "AI Services"
        G[LangGraph Agent]
        H[Gemini AI]
        I[EasyOCR]
    end
    
    subgraph "Search Services"
        J[네이버 검색 API]
        K[Exa Search API]
        L[이미지 검색]
    end
    
    subgraph "Data Layer"
        M[Memory Database]
        N[세션 저장소]
        O[캐시]
    end
    
    A --> D
    B --> F
    C --> G
    D --> E
    F --> I
    G --> H
    G --> J
    G --> K
    G --> L
    E --> M
    G --> N
    J --> O
    K --> O
    
    style A fill:#e1f5fe
    style G fill:#f3e5f5
    style M fill:#e8f5e8
```

## 개발 진행 상황
- ✅ **프로젝트 초기 설정**: 기본 구조 및 환경 설정 완료
- ✅ **FastAPI 백엔드**: API 서버 및 라우터 구현 완료
- ✅ **AI Agent 시스템**: LangGraph 기반 대화형 Agent 구현 완료
- ✅ **제품 인식 서비스**: OCR 및 AI 기반 제품 인식 구현 완료
- ✅ **이미지 검색 시스템**: 네이버 이미지 검색 API 통합 완료
- ✅ **Streamlit 프론트엔드**: 사용자 인터페이스 구현 완료
- ✅ **검색 도구 통합**: 네이버/Exa 검색 API 연동 완료
- 🔄 **API 키 설정**: 네이버 API 키 권한 설정 진행 중
- ⏳ **성능 최적화**: 검색 결과 캐싱 및 응답 속도 개선 예정
- ⏳ **테스트 코드**: 단위 테스트 및 통합 테스트 작성 예정

## 라이선스
MIT License 