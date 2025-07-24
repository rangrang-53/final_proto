"""
채팅 서비스
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from core.agent.agent_core import get_agent
from config.database import memory_db
from utils.logger import logger


class ChatService:
    """채팅 서비스"""
    
    def __init__(self):
        self.agent = get_agent()
    
    async def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """사용자 메시지 전송 및 AI 응답 생성"""
        
        logger.info(f"채팅 메시지 처리: session_id={session_id}, message={message[:50]}...")
        
        try:
            # 세션 정보 조회
            session = memory_db.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "세션을 찾을 수 없습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 제품 정보 확인
            product_info = session.get("product_info")
            if not product_info:
                return {
                    "success": False,
                    "error": "제품 분석이 완료되지 않았습니다. 먼저 제품을 분석해 주세요.",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 현재 채팅 히스토리 가져오기
            chat_history = session.get("chat_history", [])
            
            # 사용자 메시지를 히스토리에 추가
            user_message = {
                "role": "user",
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            chat_history.append(user_message)
            
            # AI Agent와 대화
            response_result = await self.agent.chat_with_user(
                message=message,
                product_info=product_info,
                session_id=session_id,
                chat_history=chat_history[:-1]  # 현재 메시지 제외한 히스토리
            )
            
            if response_result["success"]:
                # AI 응답을 히스토리에 추가
                ai_message = {
                    "role": "assistant",
                    "message": response_result["response"],
                    "timestamp": response_result["timestamp"]
                }
                chat_history.append(ai_message)
                
                # 세션에 업데이트된 히스토리 저장
                memory_db.update_session(session_id, {
                    "chat_history": chat_history,
                    "last_chat_at": datetime.now().isoformat()
                })
                
                logger.info(f"채팅 메시지 처리 완료: {len(chat_history)}개 메시지")
                
                return {
                    "success": True,
                    "data": {
                        "user_message": user_message,
                        "ai_response": ai_message,
                        "total_messages": len(chat_history)
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # AI 응답 실패 시에도 사용자 메시지는 저장
                memory_db.update_session(session_id, {
                    "chat_history": chat_history
                })
                
                logger.error(f"AI 응답 생성 실패: {response_result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": "AI 응답 생성 중 오류가 발생했습니다.",
                    "user_message": user_message,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"채팅 서비스 오류: {str(e)}")
            return {
                "success": False,
                "error": "채팅 처리 중 오류가 발생했습니다.",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """채팅 히스토리 조회"""
        
        try:
            session = memory_db.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "세션을 찾을 수 없습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            
            chat_history = session.get("chat_history", [])
            
            # 최근 메시지부터 limit 개수만큼 반환
            recent_history = chat_history[-limit:] if len(chat_history) > limit else chat_history
            
            return {
                "success": True,
                "data": {
                    "messages": recent_history,
                    "total_count": len(chat_history),
                    "returned_count": len(recent_history),
                    "product_info": session.get("product_info", {}),
                    "last_chat_at": session.get("last_chat_at", "")
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"채팅 히스토리 조회 오류: {str(e)}")
            return {
                "success": False,
                "error": "채팅 히스토리 조회 중 오류가 발생했습니다.",
                "timestamp": datetime.now().isoformat()
            }
    
    def clear_chat_history(self, session_id: str) -> Dict[str, Any]:
        """채팅 히스토리 초기화"""
        
        logger.info(f"채팅 히스토리 초기화: session_id={session_id}")
        
        try:
            session = memory_db.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "세션을 찾을 수 없습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 채팅 히스토리만 초기화 (제품 정보는 유지)
            memory_db.update_session(session_id, {
                "chat_history": [],
                "last_chat_at": None
            })
            
            logger.info("채팅 히스토리 초기화 완료")
            
            return {
                "success": True,
                "data": {
                    "message": "채팅 히스토리가 초기화되었습니다.",
                    "session_id": session_id
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"채팅 히스토리 초기화 오류: {str(e)}")
            return {
                "success": False,
                "error": "채팅 히스토리 초기화 중 오류가 발생했습니다.",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_suggested_questions(self, session_id: str) -> Dict[str, Any]:
        """제품별 추천 질문 생성"""
        
        try:
            session = memory_db.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "세션을 찾을 수 없습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            
            product_info = session.get("product_info", {})
            category = product_info.get("category", "가전제품")
            
            # 제품 카테고리별 추천 질문
            suggestions_map = {
                "에어프라이어": [
                    "기본 사용법을 알려주세요",
                    "온도와 시간 설정은 어떻게 하나요?",
                    "청소는 어떻게 해야 하나요?",
                    "어떤 음식을 조리할 수 있나요?",
                    "안전 주의사항이 있나요?"
                ],
                "전자레인지": [
                    "기본 사용법을 알려주세요",
                    "출력 조절은 어떻게 하나요?",
                    "청소 방법을 알려주세요",
                    "사용하면 안 되는 용기가 있나요?",
                    "냄새 제거 방법이 있나요?"
                ],
                "밥솥": [
                    "밥 짓는 방법을 알려주세요",
                    "물 양은 얼마나 넣어야 하나요?",
                    "청소는 어떻게 해야 하나요?",
                    "예약 취사는 어떻게 하나요?",
                    "다른 요리도 할 수 있나요?"
                ],
                "공기청정기": [
                    "기본 사용법을 알려주세요",
                    "필터 교체는 언제 해야 하나요?",
                    "청소 방법을 알려주세요",
                    "효과적인 배치 위치는 어디인가요?",
                    "전력 소비량이 궁금해요"
                ]
            }
            
            # 해당 카테고리의 추천 질문, 없으면 기본 질문
            suggestions = suggestions_map.get(category, [
                "기본 사용법을 알려주세요",
                "청소 방법을 알려주세요",
                "안전 주의사항이 있나요?",
                "고장 났을 때 어떻게 해야 하나요?",
                "효율적인 사용 팁이 있나요?"
            ])
            
            return {
                "success": True,
                "data": {
                    "suggestions": suggestions,
                    "product_category": category,
                    "total_count": len(suggestions)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"추천 질문 생성 오류: {str(e)}")
            return {
                "success": False,
                "error": "추천 질문 생성 중 오류가 발생했습니다.",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_chat_statistics(self, session_id: str) -> Dict[str, Any]:
        """채팅 통계 정보"""
        
        try:
            session = memory_db.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "세션을 찾을 수 없습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            
            chat_history = session.get("chat_history", [])
            
            # 통계 계산
            total_messages = len(chat_history)
            user_messages = len([msg for msg in chat_history if msg["role"] == "user"])
            ai_messages = len([msg for msg in chat_history if msg["role"] == "assistant"])
            
            first_chat = chat_history[0]["timestamp"] if chat_history else None
            last_chat = session.get("last_chat_at", "")
            
            return {
                "success": True,
                "data": {
                    "total_messages": total_messages,
                    "user_messages": user_messages,
                    "ai_messages": ai_messages,
                    "first_chat_at": first_chat,
                    "last_chat_at": last_chat,
                    "product_info": session.get("product_info", {})
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"채팅 통계 조회 오류: {str(e)}")
            return {
                "success": False,
                "error": "채팅 통계 조회 중 오류가 발생했습니다.",
                "timestamp": datetime.now().isoformat()
            }


# 전역 서비스 인스턴스
_service_instance: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """채팅 서비스 인스턴스 반환"""
    global _service_instance
    
    if _service_instance is None:
        _service_instance = ChatService()
    
    return _service_instance 