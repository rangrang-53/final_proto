"""
제품 인식 서비스
"""

from typing import Dict, Any, Optional
from datetime import datetime

from core.agent.agent_core import get_agent
from config.database import memory_db
from utils.logger import logger
from utils.file_utils import cleanup_temp_file


class ProductRecognitionService:
    """제품 인식 서비스"""
    
    def __init__(self):
        self.agent = get_agent()
    
    async def analyze_product(self, session_id: str) -> Dict[str, Any]:
        """세션의 업로드된 이미지에서 제품 분석"""
        
        logger.info(f"제품 분석 시작: session_id={session_id}")
        
        try:
            # 세션 정보 조회
            session = memory_db.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "세션을 찾을 수 없습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 업로드된 이미지 확인
            uploaded_image = session.get("uploaded_image")
            if not uploaded_image:
                return {
                    "success": False,
                    "error": "업로드된 이미지가 없습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            
            image_path = uploaded_image["file_path"]
            
            # AI Agent를 통한 제품 인식
            analysis_result = await self.agent.analyze_product_image(image_path, session_id)
            
            if analysis_result["success"]:
                # 세션에 제품 정보 저장
                product_info = analysis_result["product_info"]
                memory_db.update_session(session_id, {
                    "product_info": product_info,
                    "analysis_completed_at": datetime.now().isoformat()
                })
                
                # 가전제품이 아닌 경우 즉시 응답 반환
                if product_info.get("category") == "가전제품_아님":
                    logger.info(f"가전제품이 아닌 이미지로 판별됨: {product_info.get('message', '')}")
                    # 가전제품이 아닌 경우 세션에 저장하고 즉시 응답
                    memory_db.update_session(session_id, {
                        "product_info": product_info,
                        "usage_guide": "",
                        "analysis_completed_at": datetime.now().isoformat()
                    })
                    return {
                        "success": True,
                        "data": {
                            "product_info": product_info,
                            "usage_guide": "",
                            "confidence": product_info.get("confidence", 0.0),
                            "analysis_timestamp": analysis_result["timestamp"],
                            "is_appliance": False
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                
                # 가전제품인 경우 사용법 가이드 생성
                guide_result = await self.agent.generate_usage_guide(product_info, session_id)
                
                if guide_result["success"]:
                    # 사용법 가이드도 세션에 저장
                    memory_db.update_session(session_id, {
                        "usage_guide": guide_result["usage_guide"]
                    })
                
                logger.info(f"제품 분석 완료: {product_info.get('brand', 'Unknown')} {product_info.get('category', 'Unknown')}")

                
                return {
                    "success": True,
                    "data": {
                        "product_info": product_info,
                        "usage_guide": guide_result.get("usage_guide", "사용법 가이드 생성 중..."),
                        "confidence": product_info.get("confidence", 0.0),
                        "analysis_timestamp": analysis_result["timestamp"],
                        "is_appliance": True
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"제품 분석 실패: {analysis_result.get('error', 'Unknown error')}")
                return analysis_result
                
        except Exception as e:
            logger.error(f"제품 분석 서비스 오류: {str(e)}")
            return {
                "success": False,
                "error": "제품 분석 중 오류가 발생했습니다.",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_analysis_result(self, session_id: str) -> Dict[str, Any]:
        """분석 결과 조회"""
        
        try:
            session = memory_db.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "세션을 찾을 수 없습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            
            product_info = session.get("product_info")
            if not product_info:
                return {
                    "success": False,
                    "error": "분석된 제품 정보가 없습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 가전제품 여부 판별
            is_appliance = True
            if product_info.get("category") == "가전제품_아님":
                is_appliance = False
            elif not product_info.get("success", True):  # success가 False인 경우도 비가전제품
                is_appliance = False
            
            return {
                "success": True,
                "data": {
                    "data": {
                        "product_info": product_info,
                        "usage_guide": session.get("usage_guide", ""),
                        "analysis_timestamp": session.get("analysis_completed_at", ""),
                        "has_image": "uploaded_image" in session,
                        "is_appliance": is_appliance
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"분석 결과 조회 오류: {str(e)}")
            return {
                "success": False,
                "error": "분석 결과 조회 중 오류가 발생했습니다.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def reanalyze_product(self, session_id: str) -> Dict[str, Any]:
        """제품 재분석"""
        
        logger.info(f"제품 재분석 요청: session_id={session_id}")
        
        try:
            # 기존 분석 결과 초기화
            memory_db.update_session(session_id, {
                "product_info": None,
                "usage_guide": None,
                "analysis_completed_at": None
            })
            
            # 재분석 수행
            return await self.analyze_product(session_id)
            
        except Exception as e:
            logger.error(f"제품 재분석 오류: {str(e)}")
            return {
                "success": False,
                "error": "제품 재분석 중 오류가 발생했습니다.",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_supported_categories(self) -> Dict[str, Any]:
        """지원되는 제품 카테고리 목록"""
        
        categories = [
            {
                "name": "에어프라이어",
                "description": "기름 없이 바삭하게 조리하는 조리기구",
                "common_brands": ["필립스", "코스모", "쿠쿠", "리빙웰"]
            },
            {
                "name": "전자레인지",
                "description": "전자파를 이용한 가열 조리기구",
                "common_brands": ["삼성", "LG", "대우", "위니아"]
            },
            {
                "name": "밥솥",
                "description": "밥을 짓는 전자 조리기구",
                "common_brands": ["쿠쿠", "린나이", "삼성", "LG"]
            },
            {
                "name": "공기청정기",
                "description": "실내 공기를 정화하는 가전제품",
                "common_brands": ["샤오미", "LG", "삼성", "다이슨"]
            },
            {
                "name": "가습기",
                "description": "실내 습도를 조절하는 가전제품",
                "common_brands": ["쿠쿠", "위니아", "LG", "삼성"]
            },
            {
                "name": "제습기",
                "description": "실내 습도를 낮추는 가전제품",
                "common_brands": ["위니아", "LG", "삼성", "코웨이"]
            }
        ]
        
        return {
            "success": True,
            "data": {
                "categories": categories,
                "total_count": len(categories)
            },
            "timestamp": datetime.now().isoformat()
        }


# 전역 서비스 인스턴스
_service_instance: Optional[ProductRecognitionService] = None


def get_product_service() -> ProductRecognitionService:
    """제품 인식 서비스 인스턴스 반환"""
    global _service_instance
    
    if _service_instance is None:
        _service_instance = ProductRecognitionService()
    
    return _service_instance 