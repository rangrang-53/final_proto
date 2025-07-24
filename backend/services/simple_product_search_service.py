"""
간단한 제품 검색 서비스 - API 기반 제품 매칭
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
import requests
import json
from urllib.parse import quote_plus
import aiohttp

from utils.logger import logger
from config.api_keys import api_keys


class SimpleProductSearchService:
    """간단한 제품 검색 서비스 (API 기반)"""
    
    def __init__(self):
        """서비스 초기화"""
        self.search_apis = {
            "google": {
                "enabled": False,  # API 키 필요
                "url": "https://www.googleapis.com/customsearch/v1",
                "params": {
                    "key": "",  # Google API 키
                    "cx": "",   # Custom Search Engine ID
                    "searchType": "image"
                }
            },
            "naver": {
                "enabled": True,  # 무료 API
                "url": "https://openapi.naver.com/v1/search/shop.json",
                "headers": {
                    "X-Naver-Client-Id": "",  # 네이버 클라이언트 ID
                    "X-Naver-Client-Secret": ""  # 네이버 클라이언트 시크릿
                }
            }
        }
        
        # API 키 설정
        self._update_api_keys()
    
    def _update_api_keys(self):
        """API 키 업데이트"""
        # 네이버 API 키 설정
        naver_client_id, naver_client_secret = api_keys.get_naver_keys()
        if naver_client_id and naver_client_secret:
            self.search_apis["naver"]["headers"]["X-Naver-Client-Id"] = naver_client_id
            self.search_apis["naver"]["headers"]["X-Naver-Client-Secret"] = naver_client_secret
            logger.info("네이버 API 키가 설정되었습니다.")
        else:
            logger.info("네이버 API 키가 설정되지 않았습니다. 모의 검색을 사용합니다.")
        
        # Google API 키 설정 (향후 사용)
        google_api_key, google_cx = api_keys.get_google_keys()
        if google_api_key and google_cx:
            self.search_apis["google"]["params"]["key"] = google_api_key
            self.search_apis["google"]["params"]["cx"] = google_cx
            logger.info("Google API 키가 설정되었습니다.")
        
        # 브랜드별 검색 키워드 매핑
        self.brand_keywords = {
            "samsung": ["삼성", "samsung"],
            "lg": ["LG", "lg", "엘지"],
            "philips": ["필립스", "philips"],
            "cuckoo": ["쿠쿠", "cuckoo"],
            "winix": ["위닉스", "winix"],
            "dyson": ["다이슨", "dyson"],
            "sharp": ["샤프", "sharp"],
            "panasonic": ["파나소닉", "panasonic"],
            "xiaomi": ["샤오미", "xiaomi"]
        }
        
        # 카테고리별 검색 키워드
        self.category_keywords = {
            "공기청정기": ["공기청정기", "air purifier", "에어퍼리파이어"],
            "가습기": ["가습기", "humidifier", "휴미디파이어"],
            "에어프라이어": ["에어프라이어", "air fryer", "에어프라이"],
            "전자레인지": ["전자레인지", "microwave", "마이크로웨이브"],
            "밥솥": ["밥솥", "rice cooker", "라이스쿠커"],
            "세탁기": ["세탁기", "washing machine", "워싱머신"],
            "냉장고": ["냉장고", "refrigerator", "리프리지레이터"],
            "청소기": ["청소기", "vacuum cleaner", "진공청소기"],
            "선풍기": ["선풍기", "fan", "팬"]
        }
    
    async def search_product(self, brand: str, category: str, image_path: str = None) -> Dict[str, Any]:
        """제품 검색 (API 기반)"""
        
        logger.info(f"제품 검색 시작: {brand} - {category}")
        
        try:
            # 검색 쿼리 구성
            search_query = self._build_search_query(brand, category)
            
            # 네이버 쇼핑 API로 검색
            if self.search_apis["naver"]["enabled"]:
                search_result = await self._search_naver_shopping(search_query)
                if search_result["success"]:
                    return search_result
            
            # 기본 응답 (검색 실패 시)
            return {
                "success": False,
                "error": "제품 검색에 실패했습니다.",
                "message": "검색 결과를 찾을 수 없습니다."
            }
            
        except Exception as e:
            logger.error(f"제품 검색 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "검색 중 오류가 발생했습니다."
            }
    
    def _build_search_query(self, brand: str, category: str) -> str:
        """검색 쿼리 구성"""
        
        brand_keywords = self.brand_keywords.get(brand.lower(), [brand])
        category_keywords = self.category_keywords.get(category, [category])
        
        # 가장 일반적인 키워드 조합
        query_parts = []
        
        # 브랜드 키워드 (한글 우선)
        brand_keyword = brand_keywords[0] if brand_keywords else brand
        query_parts.append(brand_keyword)
        
        # 카테고리 키워드 (한글 우선)
        category_keyword = category_keywords[0] if category_keywords else category
        query_parts.append(category_keyword)
        
        # 모델명 관련 키워드 추가
        if category in ["공기청정기", "가습기"]:
            query_parts.append("모델명")
        
        return " ".join(query_parts)
    
    async def _search_naver_shopping(self, query: str) -> Dict[str, Any]:
        """네이버 쇼핑 API 검색"""
        
        try:
            # API 키 확인
            client_id = self.search_apis["naver"]["headers"]["X-Naver-Client-Id"]
            client_secret = self.search_apis["naver"]["headers"]["X-Naver-Client-Secret"]
            
            if not client_id or not client_secret:
                logger.warning("네이버 API 키가 설정되지 않음 - 모의 검색 결과 반환")
                return self._get_mock_search_results(query)
            
            # 실제 네이버 쇼핑 API 호출
            logger.info(f"네이버 쇼핑 API 검색: {query}")
            
            url = self.search_apis["naver"]["url"]
            headers = self.search_apis["naver"]["headers"]
            params = {
                "query": query,
                "display": 10,  # 검색 결과 개수
                "start": 1,     # 검색 시작 위치
                "sort": "sim"   # 정확도순 정렬
            }
            
            # 비동기 HTTP 요청
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 검색 결과 처리
                        items = data.get("items", [])
                        total = data.get("total", 0)
                        
                        logger.info(f"네이버 쇼핑 검색 완료: {len(items)}개 결과")
                        
                        return {
                            "success": True,
                            "search_method": "naver_shopping",
                            "query": query,
                            "results": items,
                            "total_count": total
                        }
                    else:
                        logger.error(f"네이버 API 오류: {response.status}")
                        return {
                            "success": False,
                            "error": f"API 오류: {response.status}"
                        }
            
        except Exception as e:
            logger.error(f"네이버 쇼핑 검색 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_mock_search_results(self, query: str) -> Dict[str, Any]:
        """모의 검색 결과 반환"""
        
        # 모의 검색 결과
        mock_results = [
            {
                "title": f"{query} 정품",
                "link": "https://example.com/product1",
                "image": "https://example.com/image1.jpg",
                "lprice": "150000",
                "hprice": "200000",
                "mallName": "공식몰",
                "productId": "12345",
                "productType": "1",
                "brand": query.split()[0],
                "maker": query.split()[0],
                "category1": "가전디지털",
                "category2": "생활가전",
                "category3": query.split()[1] if len(query.split()) > 1 else "기타",
                "category4": ""
            }
        ]
        
        return {
            "success": True,
            "search_method": "naver_shopping_mock",
            "query": query,
            "results": mock_results,
            "total_count": len(mock_results)
        }
    
    async def get_product_details(self, brand: str, category: str, image_path: str = None) -> Dict[str, Any]:
        """제품 상세 정보 조회"""
        
        logger.info(f"제품 상세 정보 조회: {brand} - {category}")
        
        # 제품 검색
        search_result = await self.search_product(brand, category, image_path)
        
        if search_result["success"]:
            results = search_result.get("results", [])
            if results:
                # 첫 번째 결과 사용
                product = results[0]
                
                return {
                    "success": True,
                    "product_details": {
                        "brand": brand,
                        "category": category,
                        "title": product.get("title", f"{brand} {category}"),
                        "model": self._extract_model_from_title(product.get("title", "")),
                        "price": product.get("lprice", "가격 정보 없음"),
                        "mall": product.get("mallName", "판매처 정보 없음"),
                        "confidence": 0.8,
                        "search_method": search_result["search_method"],
                        "similarity": 0.85
                    },
                    "message": f"제품 정보를 찾았습니다: {product.get('title', '')}"
                }
        
        return {
            "success": False,
            "error": search_result.get("error", "제품을 찾을 수 없습니다."),
            "message": "제품 정보를 찾을 수 없습니다."
        }
    
    def _extract_model_from_title(self, title: str) -> str:
        """제목에서 모델명 추출"""
        
        # 일반적인 모델명 패턴
        import re
        
        # 알파벳+숫자 패턴 (예: AP-1512H, AC-1212M)
        model_patterns = [
            r'[A-Z]{2,3}-\d{4}[A-Z]?',  # AP-1512H
            r'[A-Z]{2,3}\d{4}[A-Z]?',   # AP1512H
            r'[A-Z]{2,3}-\d{3}[A-Z]?',  # AP-512H
            r'[A-Z]{2,3}\d{3}[A-Z]?',   # AP512H
            r'\d{4}[A-Z]{2,3}',         # 1512AP
            r'[A-Z]{2,3}-\d{2}[A-Z]?',  # AP-12H
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, title.upper())
            if match:
                return match.group()
        
        # 숫자만 있는 패턴 (예: 1512, 512)
        number_match = re.search(r'\d{3,4}', title)
        if number_match:
            return number_match.group()
        
        return "모델명 확인 필요"
    
    def set_api_keys(self, google_api_key: str = "", google_cx: str = "", 
                    naver_client_id: str = "", naver_client_secret: str = ""):
        """API 키 설정"""
        
        if google_api_key and google_cx:
            self.search_apis["google"]["enabled"] = True
            self.search_apis["google"]["params"]["key"] = google_api_key
            self.search_apis["google"]["params"]["cx"] = google_cx
            logger.info("Google Custom Search API 키 설정 완료")
        
        if naver_client_id and naver_client_secret:
            self.search_apis["naver"]["enabled"] = True
            self.search_apis["naver"]["headers"]["X-Naver-Client-Id"] = naver_client_id
            self.search_apis["naver"]["headers"]["X-Naver-Client-Secret"] = naver_client_secret
            logger.info("네이버 검색 API 키 설정 완료")


# 전역 서비스 인스턴스
simple_product_search_service = SimpleProductSearchService() 