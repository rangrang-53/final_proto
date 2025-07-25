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
            
            # API 키 디버깅 로그 추가
            logger.info(f"네이버 API 키 확인 - Client ID: {client_id[:5]}... (길이: {len(client_id) if client_id else 0})")
            logger.info(f"네이버 API 키 확인 - Client Secret: {client_secret[:5]}... (길이: {len(client_secret) if client_secret else 0})")
            
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
            
            # 요청 정보 로깅
            logger.info(f"네이버 API 요청 URL: {url}")
            logger.info(f"네이버 API 요청 헤더: {headers}")
            logger.info(f"네이버 API 요청 파라미터: {params}")
            
            # 비동기 HTTP 요청
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    logger.info(f"네이버 API 응답 상태: {response.status}")
                    
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
                        # 에러 응답 내용 확인
                        error_content = await response.text()
                        logger.error(f"네이버 API 오류: {response.status}")
                        logger.error(f"네이버 API 에러 응답: {error_content}")
                        
                        # 401 에러인 경우 모의 검색으로 전환
                        if response.status == 401:
                            logger.warning("네이버 API 인증 실패 (401) - 모의 검색 모드로 전환")
                            logger.error("=== 네이버 API 키 문제 해결 방법 ===")
                            logger.error("1. 네이버 개발자 센터(https://developers.naver.com)에서 애플리케이션 확인")
                            logger.error("2. '사용 API'에서 '검색' API가 등록되어 있는지 확인")
                            logger.error("3. '웹 서비스 URL'에 'http://localhost:8501' 등록 여부 확인")
                            logger.error("4. 애플리케이션 상태가 '활성' 상태인지 확인")
                            logger.error("5. 일일 사용량 한도를 초과하지 않았는지 확인")
                            logger.error("6. Client ID와 Client Secret이 올바른지 확인")
                            logger.error("=====================================")
                            return self._get_mock_search_results(query)
                        
                        return {
                            "success": False,
                            "error": f"API 오류: {response.status}",
                            "error_details": error_content
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

    async def search_product_by_image(self, image_path: str, brand: str = None, category: str = None) -> Dict[str, Any]:
        """이미지 기반 제품 검색 (네이버 이미지 검색 API 활용)"""
        
        logger.info(f"이미지 기반 제품 검색 시작: {image_path}")
        
        try:
            # 이미지에서 텍스트 추출 (OCR)
            extracted_texts = self._extract_text_from_image(image_path)
            search_keywords = self._build_search_keywords_from_image(extracted_texts, brand, category)
            
            # 네이버 이미지 검색 API 사용
            image_search_results = await self._search_naver_images(search_keywords)
            
            if image_search_results["success"]:
                # 이미지 검색 결과에서 제품 정보 추출
                product_info = self._extract_product_info_from_images(image_search_results["results"], extracted_texts)
                
                return {
                    "success": True,
                    "search_method": "naver_image_search",
                    "product_info": product_info,
                    "search_keywords": search_keywords,
                    "total_images": len(image_search_results["results"])
                }
            else:
                logger.warning(f"네이버 이미지 검색 실패: {image_search_results.get('error', '')}")
                return {
                    "success": False,
                    "error": "이미지 검색에 실패했습니다.",
                    "fallback": True
                }
                
        except Exception as e:
            logger.error(f"이미지 기반 제품 검색 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": True
            }
    
    def _extract_text_from_image(self, image_path: str) -> List[Dict[str, Any]]:
        """이미지에서 텍스트 추출 (OCR)"""
        try:
            import easyocr
            
            # EasyOCR 초기화
            if not hasattr(self, 'ocr_reader'):
                self.ocr_reader = easyocr.Reader(['ko', 'en'])
            
            # 이미지에서 텍스트 추출
            results = self.ocr_reader.readtext(image_path)
            
            extracted_texts = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # 신뢰도 50% 이상만 사용
                    extracted_texts.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
            
            logger.info(f"이미지에서 {len(extracted_texts)}개 텍스트 추출")
            return extracted_texts
            
        except Exception as e:
            logger.warning(f"OCR 텍스트 추출 실패: {e}")
            return []
    
    def _build_search_keywords_from_image(self, extracted_texts: List[Dict], brand: str = None, category: str = None) -> List[str]:
        """이미지에서 추출된 텍스트로 검색 키워드 구성"""
        
        keywords = []
        
        # 추출된 텍스트에서 브랜드와 모델명 찾기
        for item in extracted_texts:
            text = item['text'].lower()
            
            # 브랜드 키워드 확인
            for brand_key, brand_names in self.brand_keywords.items():
                if any(brand_name in text for brand_name in brand_names):
                    if brand_key not in keywords:
                        keywords.append(brand_key)
            
            # 모델명 패턴 확인 (예: AP-1512H, HD9252 등)
            import re
            model_patterns = [
                r'[A-Z]{2,3}-\d{4}[A-Z]?',  # AP-1512H
                r'[A-Z]{2,3}\d{4}[A-Z]?',   # AP1512H
                r'[A-Z]{2,3}-\d{3}[A-Z]?',  # AP-512H
                r'[A-Z]{2,3}\d{3}[A-Z]?',   # AP512H
                r'\d{4}[A-Z]{2,3}',         # 1512AP
            ]
            
            for pattern in model_patterns:
                matches = re.findall(pattern, text.upper())
                keywords.extend(matches)
        
        # 카테고리 키워드 추가
        if category:
            category_keywords = self.category_keywords.get(category, [])
            keywords.extend(category_keywords)
        
        # 브랜드 키워드 추가
        if brand:
            brand_keywords = self.brand_keywords.get(brand.lower(), [])
            keywords.extend(brand_keywords)
        
        # 중복 제거 및 정렬
        unique_keywords = list(set(keywords))
        logger.info(f"검색 키워드 구성: {unique_keywords}")
        
        return unique_keywords
    
    async def _search_naver_images(self, keywords: List[str]) -> Dict[str, Any]:
        """네이버 이미지 검색 API 호출"""
        
        try:
            # 검색 쿼리 구성
            search_query = " ".join(keywords[:3])  # 상위 3개 키워드만 사용
            
            # 네이버 이미지 검색 API 호출
            # 실제 구현에서는 MCP Naver Search 도구 사용
            # 현재는 모의 결과 반환
            
            # TODO: 실제 네이버 이미지 검색 API 호출
            # 네이버 API 키가 정상 작동할 때 활성화
            if hasattr(self, '_naver_api_working') and self._naver_api_working:
                # 실제 네이버 이미지 검색 API 호출
                url = "https://openapi.naver.com/v1/search/image"
                headers = {
                    "X-Naver-Client-Id": self.search_apis["naver"]["headers"]["X-Naver-Client-Id"],
                    "X-Naver-Client-Secret": self.search_apis["naver"]["headers"]["X-Naver-Client-Secret"]
                }
                params = {
                    "query": search_query,
                    "display": 10,
                    "start": 1,
                    "sort": "sim"
                }
                
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                "success": True,
                                "query": search_query,
                                "results": data.get("items", []),
                                "total_count": data.get("total", 0)
                            }
                        else:
                            logger.warning(f"네이버 이미지 검색 API 실패: {response.status}")
                            return self._get_mock_image_results(search_query)
            else:
                # 모의 결과 반환
                return self._get_mock_image_results(search_query)
            
        except Exception as e:
            logger.error(f"네이버 이미지 검색 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_mock_image_results(self, search_query: str) -> Dict[str, Any]:
        """모의 이미지 검색 결과 반환"""
        
        mock_image_results = [
            {
                "title": f"{search_query} 제품 이미지",
                "link": "https://example.com/image1.jpg",
                "thumbnail": "https://example.com/thumb1.jpg",
                "sizeheight": "300",
                "sizewidth": "400"
            },
            {
                "title": f"{search_query} 모델 이미지",
                "link": "https://example.com/image2.jpg", 
                "thumbnail": "https://example.com/thumb2.jpg",
                "sizeheight": "300",
                "sizewidth": "400"
            }
        ]
        
        return {
            "success": True,
            "query": search_query,
            "results": mock_image_results,
            "total_count": len(mock_image_results)
        }
    
    def _extract_product_info_from_images(self, image_results: List[Dict], extracted_texts: List[Dict]) -> Dict[str, Any]:
        """이미지 검색 결과에서 제품 정보 추출"""
        
        try:
            # 추출된 텍스트에서 브랜드와 모델명 찾기
            brand = "불분명"
            model = "확인 불가"
            
            for item in extracted_texts:
                text = item['text'].lower()
                
                # 브랜드 확인
                for brand_key, brand_names in self.brand_keywords.items():
                    if any(brand_name in text for brand_name in brand_names):
                        brand = brand_key.upper()
                        break
                
                # 모델명 확인
                import re
                model_patterns = [
                    r'[A-Z]{2,3}-\d{4}[A-Z]?',  # AP-1512H
                    r'[A-Z]{2,3}\d{4}[A-Z]?',   # AP1512H
                    r'[A-Z]{2,3}-\d{3}[A-Z]?',  # AP-512H
                    r'[A-Z]{2,3}\d{3}[A-Z]?',   # AP512H
                ]
                
                for pattern in model_patterns:
                    match = re.search(pattern, text.upper())
                    if match:
                        model = match.group()
                        break
            
            # 카테고리 추정
            category = self._estimate_category_from_texts(extracted_texts)
            
            return {
                "brand": brand,
                "model": model,
                "category": category,
                "confidence": 0.8,
                "search_method": "image_based",
                "extracted_texts": [item['text'] for item in extracted_texts]
            }
            
        except Exception as e:
            logger.error(f"제품 정보 추출 실패: {e}")
            return {
                "brand": "불분명",
                "model": "확인 불가", 
                "category": "기타",
                "confidence": 0.3,
                "search_method": "image_based",
                "extracted_texts": []
            }
    
    def _estimate_category_from_texts(self, extracted_texts: List[Dict]) -> str:
        """추출된 텍스트에서 카테고리 추정"""
        
        all_text = " ".join([item['text'].lower() for item in extracted_texts])
        
        # 카테고리별 키워드 매칭
        for category, keywords in self.category_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                return category
        
        return "기타"


# 전역 서비스 인스턴스
simple_product_search_service = SimpleProductSearchService() 