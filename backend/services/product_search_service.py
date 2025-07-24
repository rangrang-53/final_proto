"""
브랜드별 제품 검색 서비스 - 웹 스크래핑 기반 제품 매칭
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import cv2
import numpy as np
from PIL import Image
import io
import base64
from urllib.parse import urljoin, urlparse
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from utils.logger import logger


class ProductSearchService:
    """브랜드별 제품 검색 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.driver = None
        self.similarity_threshold = 0.7  # 이미지 유사도 임계값
        
        # 브랜드별 검색 설정
        self.brand_search_configs = {
            "samsung": {
                "name": "삼성전자",
                "search_url": "https://www.samsung.com/sec/search/",
                "product_selector": ".product-item",
                "image_selector": ".product-image img",
                "title_selector": ".product-title",
                "model_selector": ".product-model",
                "search_params": {"q": ""}
            },
            "lg": {
                "name": "LG전자",
                "search_url": "https://www.lge.co.kr/sch?keyword=",
                "product_selector": ".product-card",
                "image_selector": ".product-img img",
                "title_selector": ".product-name",
                "model_selector": ".product-code",
                "search_params": {"keyword": ""}
            },
            "philips": {
                "name": "필립스",
                "search_url": "https://www.philips.co.kr/search/",
                "product_selector": ".product-item",
                "image_selector": ".product-image img",
                "title_selector": ".product-title",
                "model_selector": ".product-model",
                "search_params": {"q": ""}
            },
            "cuckoo": {
                "name": "쿠쿠",
                "search_url": "https://www.cuckoo.co.kr/searchWord?searchWord=",
                "product_selector": ".product-item",
                "image_selector": ".product-image img",
                "title_selector": ".product-title",
                "model_selector": ".product-model",
                "search_params": {"keyword": ""}
            },
            "winix": {
                "name": "위닉스",
                "search_url": "https://www.winix.com/search/",
                "product_selector": ".product-item",
                "image_selector": ".product-image img",
                "title_selector": ".product-title",
                "model_selector": ".product-model",
                "search_params": {"q": ""}
            }
        }
        
        # 대체 검색 사이트 (공식 사이트 접근이 어려운 경우)
        self.fallback_search_sites = [
            "https://www.google.com/search?tbm=shop&q=",
            "https://search.naver.com/search.naver?where=shopping&query=",
            "https://shopping.daum.net/search?q="
        ]
    
    def _initialize_driver(self):
        """Selenium WebDriver 초기화"""
        if self.driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")  # 헤드리스 모드
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                
                self.driver = webdriver.Chrome(
                    service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                logger.info("Selenium WebDriver 초기화 완료")
            except Exception as e:
                logger.error(f"WebDriver 초기화 실패: {e}")
                self.driver = None
    
    def _cleanup_driver(self):
        """WebDriver 정리"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("WebDriver 정리 완료")
            except Exception as e:
                logger.error(f"WebDriver 정리 실패: {e}")
    
    async def search_product_by_brand(self, brand: str, category: str, image_path: str) -> Dict[str, Any]:
        """브랜드별 제품 검색 및 이미지 유사도 비교"""
        
        logger.info(f"브랜드별 제품 검색 시작: {brand} - {category}")
        
        try:
            # WebDriver 초기화
            self._initialize_driver()
            if not self.driver:
                return self._fallback_search(brand, category, image_path)
            
            # 브랜드 설정 확인
            if brand not in self.brand_search_configs:
                logger.warning(f"지원하지 않는 브랜드: {brand}")
                return self._fallback_search(brand, category, image_path)
            
            config = self.brand_search_configs[brand]
            
            # 검색어 구성
            search_query = f"{config['name']} {category}"
            
            # 브랜드 공식 사이트에서 검색
            products = await self._search_official_site(config, search_query)
            
            if not products:
                logger.info(f"공식 사이트에서 제품을 찾을 수 없음: {brand}")
                return self._fallback_search(brand, category, image_path)
            
            # 이미지 유사도 비교
            best_match = await self._compare_image_similarity(products, image_path)
            
            if best_match:
                logger.info(f"제품 매칭 성공: {best_match['title']} (유사도: {best_match['similarity']:.2f})")
                return {
                    "success": True,
                    "matched_product": best_match,
                    "search_method": "official_site",
                    "total_products": len(products)
                }
            else:
                logger.info("유사한 제품을 찾을 수 없음")
                return self._fallback_search(brand, category, image_path)
                
        except Exception as e:
            logger.error(f"브랜드별 제품 검색 실패: {e}")
            return self._fallback_search(brand, category, image_path)
        finally:
            self._cleanup_driver()
    
    async def _search_official_site(self, config: Dict, search_query: str) -> List[Dict]:
        """브랜드 공식 사이트에서 제품 검색"""
        
        products = []
        
        try:
            # 검색 URL 구성
            search_url = config["search_url"]
            params = config["search_params"].copy()
            params[list(params.keys())[0]] = search_query
            
            # URL에 파라미터 추가
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{search_url}?{param_str}"
            
            logger.info(f"공식 사이트 검색: {full_url}")
            
            # 페이지 로드
            self.driver.get(full_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, config["product_selector"]))
            )
            
            # 제품 목록 추출
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, config["product_selector"])
            
            for element in product_elements[:10]:  # 상위 10개 제품만 처리
                try:
                    # 제품 정보 추출
                    title = element.find_element(By.CSS_SELECTOR, config["title_selector"]).text
                    image_element = element.find_element(By.CSS_SELECTOR, config["image_selector"])
                    image_url = image_element.get_attribute("src")
                    
                    # 모델명 추출 (있는 경우)
                    try:
                        model = element.find_element(By.CSS_SELECTOR, config["model_selector"]).text
                    except NoSuchElementException:
                        model = ""
                    
                    if image_url and title:
                        products.append({
                            "title": title,
                            "model": model,
                            "image_url": image_url,
                            "source": "official_site"
                        })
                        
                except Exception as e:
                    logger.warning(f"제품 정보 추출 실패: {e}")
                    continue
            
            logger.info(f"공식 사이트에서 {len(products)}개 제품 발견")
            return products
            
        except TimeoutException:
            logger.warning("페이지 로드 시간 초과")
            return []
        except Exception as e:
            logger.error(f"공식 사이트 검색 실패: {e}")
            return []
    
    async def _fallback_search(self, brand: str, category: str, image_path: str) -> Dict[str, Any]:
        """대체 검색 사이트에서 제품 검색"""
        
        logger.info(f"대체 검색 사이트에서 검색: {brand} - {category}")
        
        try:
            search_query = f"{brand} {category}"
            
            for site in self.fallback_search_sites:
                try:
                    products = await self._search_fallback_site(site, search_query)
                    if products:
                        best_match = await self._compare_image_similarity(products, image_path)
                        if best_match:
                            return {
                                "success": True,
                                "matched_product": best_match,
                                "search_method": "fallback_site",
                                "total_products": len(products)
                            }
                except Exception as e:
                    logger.warning(f"대체 사이트 검색 실패 ({site}): {e}")
                    continue
            
            return {
                "success": False,
                "error": "제품을 찾을 수 없습니다.",
                "search_method": "fallback_site"
            }
            
        except Exception as e:
            logger.error(f"대체 검색 실패: {e}")
            return {
                "success": False,
                "error": "검색 중 오류가 발생했습니다.",
                "search_method": "fallback_site"
            }
    
    async def _search_fallback_site(self, site_url: str, search_query: str) -> List[Dict]:
        """대체 검색 사이트에서 제품 검색"""
        
        products = []
        
        try:
            # HTTP 요청으로 검색
            full_url = f"{site_url}{search_query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(full_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # HTML 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제품 이미지 찾기 (일반적인 셀렉터들)
            image_selectors = [
                "img[src*='product']",
                "img[src*='item']",
                ".product img",
                ".item img",
                "[class*='product'] img",
                "[class*='item'] img"
            ]
            
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images[:20]:  # 상위 20개 이미지만 처리
                    try:
                        src = img.get("src")
                        if src and not src.startswith("data:"):
                            # 절대 URL로 변환
                            if not src.startswith("http"):
                                src = urljoin(site_url, src)
                            
                            # 제품명 추출 (근처 텍스트에서)
                            title = self._extract_product_title(img)
                            
                            products.append({
                                "title": title or f"제품 ({len(products) + 1})",
                                "model": "",
                                "image_url": src,
                                "source": "fallback_site"
                            })
                    except Exception as e:
                        continue
            
            logger.info(f"대체 사이트에서 {len(products)}개 제품 발견")
            return products
            
        except Exception as e:
            logger.error(f"대체 사이트 검색 실패: {e}")
            return []
    
    def _extract_product_title(self, img_element) -> str:
        """이미지 요소에서 제품명 추출"""
        
        try:
            # 이미지의 alt 속성
            alt = img_element.get("alt", "")
            if alt:
                return alt
            
            # 부모 요소에서 텍스트 찾기
            parent = img_element.parent
            if parent:
                # 제목 관련 클래스나 ID를 가진 요소 찾기
                title_selectors = [
                    ".title", ".name", ".product-name", ".item-name",
                    "[class*='title']", "[class*='name']"
                ]
                
                for selector in title_selectors:
                    title_elem = parent.select_one(selector)
                    if title_elem and title_elem.text.strip():
                        return title_elem.text.strip()
                
                # 부모 요소의 텍스트
                text = parent.get_text().strip()
                if text and len(text) < 100:  # 너무 긴 텍스트는 제외
                    return text
            
            return ""
            
        except Exception:
            return ""
    
    async def _compare_image_similarity(self, products: List[Dict], target_image_path: str) -> Optional[Dict]:
        """이미지 유사도 비교"""
        
        try:
            # 타겟 이미지 로드
            target_image = cv2.imread(target_image_path)
            if target_image is None:
                logger.error("타겟 이미지를 로드할 수 없습니다.")
                return None
            
            target_features = self._extract_image_features(target_image)
            
            best_match = None
            best_similarity = 0
            
            for product in products:
                try:
                    # 제품 이미지 다운로드
                    product_image = await self._download_image(product["image_url"])
                    if product_image is None:
                        continue
                    
                    # 이미지 특징 추출
                    product_features = self._extract_image_features(product_image)
                    
                    # 유사도 계산
                    similarity = self._calculate_similarity(target_features, product_features)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = {
                            **product,
                            "similarity": similarity
                        }
                    
                    # 메모리 정리
                    del product_image
                    
                except Exception as e:
                    logger.warning(f"제품 이미지 처리 실패: {e}")
                    continue
            
            # 임계값 이상인 경우만 반환
            if best_match and best_match["similarity"] >= self.similarity_threshold:
                return best_match
            
            return None
            
        except Exception as e:
            logger.error(f"이미지 유사도 비교 실패: {e}")
            return None
    
    async def _download_image(self, image_url: str) -> Optional[np.ndarray]:
        """이미지 다운로드"""
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 이미지 데이터를 numpy 배열로 변환
            image_data = np.frombuffer(response.content, np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            
            return image
            
        except Exception as e:
            logger.warning(f"이미지 다운로드 실패 ({image_url}): {e}")
            return None
    
    def _extract_image_features(self, image: np.ndarray) -> Dict[str, Any]:
        """이미지 특징 추출"""
        
        try:
            # 이미지 크기 통일
            image = cv2.resize(image, (224, 224))
            
            # HSV 색상 공간으로 변환
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 색상 히스토그램
            color_hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            color_hist = cv2.normalize(color_hist, color_hist).flatten()
            
            # 엣지 특징
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # 텍스처 특징 (간단한 통계)
            texture_features = [
                np.mean(gray),
                np.std(gray),
                np.var(gray)
            ]
            
            return {
                "color_hist": color_hist,
                "edge_density": edge_density,
                "texture_features": texture_features
            }
            
        except Exception as e:
            logger.error(f"이미지 특징 추출 실패: {e}")
            return {}
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """이미지 특징 간 유사도 계산"""
        
        try:
            if not features1 or not features2:
                return 0.0
            
            similarity_score = 0.0
            weights = {"color": 0.5, "edge": 0.3, "texture": 0.2}
            
            # 색상 히스토그램 유사도
            if "color_hist" in features1 and "color_hist" in features2:
                color_sim = cv2.compareHist(
                    features1["color_hist"], 
                    features2["color_hist"], 
                    cv2.HISTCMP_CORREL
                )
                similarity_score += weights["color"] * max(0, color_sim)
            
            # 엣지 밀도 유사도
            if "edge_density" in features1 and "edge_density" in features2:
                edge_sim = 1 - abs(features1["edge_density"] - features2["edge_density"])
                similarity_score += weights["edge"] * max(0, edge_sim)
            
            # 텍스처 특징 유사도
            if "texture_features" in features1 and "texture_features" in features2:
                texture_sim = 1 - np.mean(np.abs(
                    np.array(features1["texture_features"]) - 
                    np.array(features2["texture_features"])
                )) / 255
                similarity_score += weights["texture"] * max(0, texture_sim)
            
            return similarity_score
            
        except Exception as e:
            logger.error(f"유사도 계산 실패: {e}")
            return 0.0
    
    async def get_product_details(self, brand: str, category: str, image_path: str) -> Dict[str, Any]:
        """제품 상세 정보 조회 (검색 + 매칭)"""
        
        logger.info(f"제품 상세 정보 조회: {brand} - {category}")
        
        # 브랜드별 제품 검색
        search_result = await self.search_product_by_brand(brand, category, image_path)
        
        if search_result["success"]:
            matched_product = search_result["matched_product"]
            
            # 제품 상세 정보 구성
            product_details = {
                "brand": brand,
                "category": category,
                "title": matched_product["title"],
                "model": matched_product.get("model", ""),
                "similarity": matched_product["similarity"],
                "search_method": search_result["search_method"],
                "image_url": matched_product["image_url"],
                "confidence": min(matched_product["similarity"] * 1.2, 1.0)  # 신뢰도 조정
            }
            
            return {
                "success": True,
                "product_details": product_details,
                "message": f"제품 매칭 성공: {matched_product['title']}"
            }
        else:
            return {
                "success": False,
                "error": search_result.get("error", "제품을 찾을 수 없습니다."),
                "message": "제품 매칭에 실패했습니다."
            }


# 전역 서비스 인스턴스
product_search_service = ProductSearchService() 