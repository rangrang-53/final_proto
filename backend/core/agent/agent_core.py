"""
LangGraph 기반 AI Agent 핵심 구현
"""

import json
from typing import Dict, Any, List, Optional, Sequence
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from config.settings import settings
from utils.logger import logger
from core.agent.prompts.system_prompts import (
    PRODUCT_RECOGNITION_PROMPT,
    USAGE_GUIDE_PROMPT,
    GENERAL_CHAT_PROMPT
)
from core.agent.tools.search_tools import AVAILABLE_TOOLS


class ApplianceAgent:
    """가전제품 사용법 안내 AI Agent"""
    
    def __init__(self):
        """Agent 초기화"""
        self.model = None
        self.product_recognition_agent = None
        self.chat_agent = None
        self.checkpointer = MemorySaver()
        self._initialize_model()
        self._initialize_agents()
    
    def _initialize_model(self):
        """Gemini 모델 초기화"""
        try:
            self.model = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.google_api_key,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                convert_system_message_to_human=True  # Gemini는 system message를 human으로 변환
            )
            logger.info(f"Gemini 모델 초기화 완료: {settings.gemini_model}")
        except Exception as e:
            logger.error(f"Gemini 모델 초기화 실패: {str(e)}")
            raise
    
    def _initialize_agents(self):
        """LangGraph Agent들 초기화"""
        try:
            # 제품 인식용 Agent (도구 없음)
            self.product_recognition_agent = create_react_agent(
                self.model,
                tools=[],  # 제품 인식은 도구 없이 Vision만 사용
                checkpointer=self.checkpointer
            )
            
            # 대화용 Agent (검색 도구 포함)
            self.chat_agent = create_react_agent(
                self.model,
                tools=AVAILABLE_TOOLS,
                checkpointer=self.checkpointer
            )
            
            logger.info("LangGraph Agent 초기화 완료")
            
        except Exception as e:
            logger.error(f"LangGraph Agent 초기화 실패: {str(e)}")
            raise
    
    async def analyze_product_image(self, image_path: str, session_id: str) -> Dict[str, Any]:
        """이미지에서 제품 인식 및 분석"""
        
        logger.info(f"제품 이미지 분석 시작: {image_path}")
        
        try:
            # 먼저 product_recognition_service의 결과 확인
            from services.product_recognition_service import ProductRecognitionService
            recognition_service = ProductRecognitionService()
            recognition_result = recognition_service.classify_product_category(image_path)
            
            # 가전제품이 아닌 경우 즉시 반환
            if not recognition_result.get("success", True) or recognition_result.get("category") == "가전제품_아님":
                logger.info(f"가전제품이 아닌 것으로 판별됨: {recognition_result.get('message', '')}")
                return {
                    "success": True,
                    "product_info": {
                        "brand": recognition_result.get("brand", "해당없음"),
                        "category": recognition_result.get("category", "가전제품_아님"),
                        "model": "해당없음",
                        "confidence": recognition_result.get("confidence", 0.0),
                        "description": recognition_result.get("message", "가전제품이 아닙니다."),
                        "features": [],
                        "extracted_texts": recognition_result.get("extracted_texts", [])
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            # 이미지를 base64로 인코딩
            import base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode()
            
            # 시스템 프롬프트와 이미지 메시지 구성
            messages = [
                HumanMessage(content=[
                    {"type": "text", "text": PRODUCT_RECOGNITION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    }
                ])
            ]
            
            # Agent 실행
            config = {"configurable": {"thread_id": f"recognition_{session_id}"}}
            response = self.product_recognition_agent.invoke(
                {"messages": messages}, 
                config=config
            )
            
            # 응답에서 제품 정보 추출
            ai_message = response["messages"][-1]
            
            try:
                # JSON 형식의 응답 파싱 시도
                content = ai_message.content.strip()
                # JSON 부분만 추출 (중괄호로 시작하고 끝나는 부분)
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    product_info = json.loads(json_content)
                else:
                    # JSON을 찾을 수 없는 경우
                    raise json.JSONDecodeError("JSON not found", content, 0)
                    
            except json.JSONDecodeError as e:
                # JSON 파싱 실패 시 텍스트에서 브랜드와 카테고리 추출 시도
                logger.warning(f"제품 인식 응답이 JSON 형식이 아님: {e}")
                logger.warning(f"AI 응답: {ai_message.content}")
                
                # AI 응답에서 브랜드와 카테고리 추출 시도
                content = ai_message.content.lower()
                extracted_brand = "불분명"
                extracted_category = "가전제품"
                
                # 브랜드 추출
                brand_patterns = {
                    "samsung": ["samsung", "삼성", "갤럭시"],
                    "lg": ["lg", "엘지"],
                    "philips": ["philips", "필립스"],
                    "cuckoo": ["cuckoo", "쿠쿠"],
                    "winix": ["winix", "위닉스"],
                    "xiaomi": ["xiaomi", "샤오미"],
                    "dyson": ["dyson", "다이슨"],
                    "sharp": ["sharp", "샤프"],
                    "panasonic": ["panasonic", "파나소닉"]
                }
                
                for brand, patterns in brand_patterns.items():
                    if any(pattern in content for pattern in patterns):
                        extracted_brand = brand
                        break
                
                # 카테고리 추출
                category_patterns = {
                    "가습기": ["가습기", "humidifier"],
                    "에어프라이어": ["에어프라이어", "air fryer"],
                    "전자레인지": ["전자레인지", "microwave"],
                    "밥솥": ["밥솥", "rice cooker"],
                    "공기청정기": ["공기청정기", "air purifier"],
                    "세탁기": ["세탁기", "washing machine"],
                    "냉장고": ["냉장고", "refrigerator"],
                    "청소기": ["청소기", "vacuum"],
                    "선풍기": ["선풍기", "fan"]
                }
                
                for category, patterns in category_patterns.items():
                    if any(pattern in content for pattern in patterns):
                        extracted_category = category
                        break
                
                # OCR 결과가 있으면 활용
                session = memory_db.get_session(session_id)
                recognition_result = session.get("product_recognition", {})
                
                product_info = {
                    "brand": recognition_result.get("brand", extracted_brand),
                    "category": recognition_result.get("category", extracted_category),
                    "model": recognition_result.get("model", "모델 미상"),
                    "confidence": recognition_result.get("confidence", 0.5),
                    "description": ai_message.content,
                    "features": [],
                    "extracted_texts": recognition_result.get("extracted_texts", [])
                }
            
            logger.info(f"제품 인식 완료: {product_info.get('brand', 'Unknown')} {product_info.get('category', 'Unknown')}")
            
            return {
                "success": True,
                "product_info": product_info,
                "raw_response": ai_message.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"제품 이미지 분석 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_usage_guide(self, product_info: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """제품 사용법 가이드 생성"""
        
        logger.info(f"사용법 가이드 생성: {product_info.get('brand', 'Unknown')} {product_info.get('category', 'Unknown')}")
        
        try:
            # 제품 정보를 바탕으로 프롬프트 구성
            system_prompt = USAGE_GUIDE_PROMPT.format(
                product_brand=product_info.get('brand', '알 수 없음'),
                product_category=product_info.get('category', '가전제품'),
                product_model=product_info.get('model', '모델 미상')
            )
            
            messages = [
                HumanMessage(content=f"{system_prompt}\n\n이 제품의 기본 사용법을 단계별로 알려주세요. 안전 주의사항도 포함해 주세요.")
            ]
            
            # Agent 실행
            config = {"configurable": {"thread_id": f"guide_{session_id}"}}
            response = self.chat_agent.invoke(
                {"messages": messages}, 
                config=config
            )
            
            ai_message = response["messages"][-1]
            
            logger.info("사용법 가이드 생성 완료")
            
            return {
                "success": True,
                "usage_guide": ai_message.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"사용법 가이드 생성 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def chat_with_user(self, message: str, product_info: Dict[str, Any], session_id: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """사용자와 대화"""
        
        logger.info(f"사용자 대화 처리: {message[:50]}...")
        
        try:
            # 제품 정보를 문자열로 변환
            product_str = f"{product_info.get('brand', '알 수 없음')} {product_info.get('category', '가전제품')} {product_info.get('model', '모델 미상')}"
            
            # 시스템 프롬프트 구성
            system_prompt = GENERAL_CHAT_PROMPT.format(product_info=product_str)
            
            # 메시지 구성
            messages = [HumanMessage(content=system_prompt)]
            
            # 이전 대화 히스토리 추가
            if chat_history:
                for chat in chat_history[-10:]:  # 최근 10개 메시지만 유지
                    if chat["role"] == "user":
                        messages.append(HumanMessage(content=chat["message"]))
                    else:
                        messages.append(AIMessage(content=chat["message"]))
            
            # 현재 사용자 메시지 추가
            messages.append(HumanMessage(content=message))
            
            # Agent 실행
            config = {"configurable": {"thread_id": f"chat_{session_id}"}}
            response = self.chat_agent.invoke(
                {"messages": messages}, 
                config=config
            )
            
            ai_message = response["messages"][-1]
            
            logger.info("사용자 대화 처리 완료")
            
            return {
                "success": True,
                "response": ai_message.content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"사용자 대화 처리 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요.",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Agent 상태 확인"""
        return {
            "model_initialized": self.model is not None,
            "product_agent_ready": self.product_recognition_agent is not None,
            "chat_agent_ready": self.chat_agent is not None,
            "model_name": settings.gemini_model,
            "tools_count": len(AVAILABLE_TOOLS),
            "timestamp": datetime.now().isoformat()
        }


# 전역 Agent 인스턴스
_agent_instance: Optional[ApplianceAgent] = None


def get_agent() -> ApplianceAgent:
    """Agent 인스턴스 반환 (싱글톤 패턴)"""
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = ApplianceAgent()
    
    return _agent_instance


async def initialize_agent():
    """Agent 초기화 (앱 시작 시 호출)"""
    try:
        agent = get_agent()
        status = agent.get_agent_status()
        logger.info(f"Agent 초기화 완료: {status}")
        return True
    except Exception as e:
        logger.error(f"Agent 초기화 실패: {str(e)}")
        return False 