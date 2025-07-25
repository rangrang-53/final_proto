"""
제품 인식 서비스 - OCR 기반 브랜드 검출 및 확신도 기반 분류
"""

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("EasyOCR not available, using fallback mode")

import cv2
import numpy as np
from PIL import Image
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from utils.logger import logger
from .simple_product_search_service import simple_product_search_service


class ProductRecognitionService:
    """제품 인식 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.ocr_reader = None
        self.confidence_threshold = 0.7  # 확신도 임계값
        
        # 가전제품 필터링을 위한 객체 탐지 카테고리
        self.appliance_categories = [
            "appliance", "electronics", "device", "machine", "equipment",
            "refrigerator", "microwave", "oven", "dishwasher", "washing machine",
            "dryer", "vacuum", "fan", "air conditioner", "heater", "humidifier",
            "air purifier", "rice cooker", "blender", "toaster", "coffee maker"
        ]
        
        # 가전제품이 아닌 것으로 분류되는 카테고리들
        self.non_appliance_categories = [
            "person", "people", "human", "face", "head", "body",
            "animal", "cat", "dog", "bird", "fish", "pet",
            "food", "fruit", "vegetable", "meat", "bread", "cake",
            "furniture", "chair", "table", "bed", "sofa", "desk",
            "clothing", "shirt", "pants", "dress", "shoes", "hat",
            "vehicle", "car", "bike", "motorcycle", "bus", "truck",
            "building", "house", "office", "store", "school",
            "nature", "tree", "flower", "grass", "mountain", "sea"
        ]
        
        # 브랜드별 제품 카테고리 매핑
        self.brand_categories = {
            "samsung": ["가습기", "공기청정기", "에어프라이어", "전자레인지", "밥솥", "세탁기", "냉장고"],
            "lg": ["가습기", "공기청정기", "에어프라이어", "전자레인지", "밥솥", "세탁기", "냉장고", "스타일러"],
            "philips": ["에어프라이어", "전기면도기", "칫솔", "공기청정기"],
            "cuckoo": ["밥솥", "정수기", "공기청정기"],
            "winix": ["공기청정기", "가습기", "제습기"],
            "xiaomi": ["공기청정기", "가습기", "로봇청소기", "전기밥솥"],
            "dyson": ["청소기", "헤어드라이어", "공기청정기", "선풍기"],
            "sharp": ["공기청정기", "가습기", "전자레인지"],
            "panasonic": ["전자레인지", "밥솥", "헤어드라이어"]
        }
        
        # 제품 카테고리별 특징적 키워드
        self.category_keywords = {
            "가습기": ["humidifier", "mist", "water", "tank", "물탱크", "가습", "습도"],
            "공기청정기": ["air purifier", "hepa", "filter", "공기", "정화", "필터"],
            "에어프라이어": ["air fryer", "basket", "바스켓", "튀김", "오일프리"],
            "전자레인지": ["microwave", "micro", "전자레인지", "데우기"],
            "밥솥": ["rice cooker", "pressure", "밥솥", "취사", "압력"],
            "세탁기": ["washing machine", "wash", "세탁", "드럼"],
            "냉장고": ["refrigerator", "fridge", "냉장", "냉동"],
            "청소기": ["vacuum", "cleaner", "청소", "먼지"],
            "선풍기": ["fan", "선풍기", "바람"]
        }
    
    def _initialize_ocr(self):
        """OCR 리더 초기화 (지연 초기화)"""
        if not EASYOCR_AVAILABLE:
            logger.info("EasyOCR이 설치되지 않음 - 기본 분류 모드로 실행")
            return
            
        if self.ocr_reader is None:
            try:
                logger.info("EasyOCR 초기화 중...")
                # GPU 사용 불가능한 경우 CPU 모드로 실행
                self.ocr_reader = easyocr.Reader(['ko', 'en'], gpu=False, verbose=False)
                logger.info("EasyOCR 초기화 완료")
            except Exception as e:
                logger.error(f"EasyOCR 초기화 실패: {e}")
                logger.info("OCR 없이 기본 분류 모드로 실행합니다.")
                self.ocr_reader = None
    
    def is_appliance_image(self, image_path: str) -> Dict[str, Any]:
        """이미지가 가전제품인지 판별"""
        try:
            # 이미지에서 텍스트 추출
            extracted_texts = self.extract_text_from_image(image_path)
            all_text = " ".join([item['text'].lower() for item in extracted_texts])
            
            # 브랜드 검출
            detected_brand = self.detect_brand_from_text(extracted_texts)
            
            # 브랜드가 검출된 경우 가전제품으로 판단
            if detected_brand:
                logger.info(f"브랜드 검출로 가전제품 판별: {detected_brand}")
                return {
                    "is_appliance": True,
                    "confidence": 0.9,
                    "reason": f"브랜드 '{detected_brand}' 검출",
                    "detected_brand": detected_brand
                }
            
            # 텍스트 기반 가전제품 키워드 검사
            appliance_keywords = [
                "humidifier", "air purifier", "microwave", "refrigerator", "washing machine",
                "vacuum", "fan", "rice cooker", "blender", "toaster", "coffee maker",
                "가습기", "공기청정기", "전자레인지", "냉장고", "세탁기", "청소기", "선풍기", "밥솥"
            ]
            
            found_appliance_keywords = []
            for keyword in appliance_keywords:
                if keyword.lower() in all_text:
                    found_appliance_keywords.append(keyword)
            
            if found_appliance_keywords:
                logger.info(f"가전제품 키워드 검출: {found_appliance_keywords}")
                return {
                    "is_appliance": True,
                    "confidence": 0.8,
                    "reason": f"가전제품 키워드 검출: {', '.join(found_appliance_keywords)}",
                    "detected_keywords": found_appliance_keywords
                }
            
            # 가전제품이 아닌 키워드 검사 (확장)
            non_appliance_keywords = [
                "cat", "dog", "animal", "pet", "person", "human", "face", "head", "body",
                "food", "fruit", "vegetable", "cake", "bread", "meat", "fish", "chicken",
                "car", "bike", "motorcycle", "bus", "truck", "vehicle", "transport",
                "tree", "flower", "grass", "mountain", "sea", "nature", "landscape",
                "house", "building", "office", "store", "school", "architecture",
                "chair", "table", "bed", "sofa", "desk", "furniture",
                "shirt", "pants", "dress", "shoes", "hat", "clothing", "fashion",
                "book", "magazine", "newspaper", "document", "paper",
                "고양이", "강아지", "동물", "사람", "얼굴", "머리", "몸",
                "음식", "과일", "채소", "케이크", "빵", "고기", "생선", "닭고기",
                "자동차", "자전거", "오토바이", "버스", "트럭", "교통수단",
                "나무", "꽃", "풀", "산", "바다", "자연", "풍경",
                "집", "건물", "사무실", "상점", "학교", "건축",
                "의자", "테이블", "침대", "소파", "책상", "가구",
                "셔츠", "바지", "드레스", "신발", "모자", "옷", "패션",
                "책", "잡지", "신문", "문서", "종이",
                # 추가 동물 관련 키워드
                "feline", "canine", "mammal", "creature", "beast",
                "고양이과", "개과", "포유류", "생물", "짐승"
            ]
            
            found_non_appliance_keywords = []
            for keyword in non_appliance_keywords:
                if keyword.lower() in all_text:
                    found_non_appliance_keywords.append(keyword)
            
            if found_non_appliance_keywords:
                logger.info(f"비가전제품 키워드 검출: {found_non_appliance_keywords}")
                return {
                    "is_appliance": False,
                    "confidence": 0.9,
                    "reason": f"비가전제품 키워드 검출: {', '.join(found_non_appliance_keywords)}",
                    "detected_keywords": found_non_appliance_keywords
                }
            
            # 이미지 특징 기반 판별 (더 엄격한 기준)
            image_features = self._analyze_appliance_image_features(image_path)
            
            # 가전제품 판별을 더 엄격하게: 가전제품 점수가 비가전제품 점수보다 충분히 높아야 함
            appliance_threshold = 0.3  # 가전제품 판별을 위한 최소 점수 차이
            score_diff = image_features["appliance_score"] - image_features["non_appliance_score"]
            
            if score_diff > appliance_threshold and image_features["appliance_score"] > 0.6:
                return {
                    "is_appliance": True,
                    "confidence": image_features["appliance_score"],
                    "reason": "이미지 특징 분석 결과 가전제품으로 판별",
                    "image_features": image_features
                }
            else:
                return {
                    "is_appliance": False,
                    "confidence": image_features["non_appliance_score"],
                    "reason": "이미지 특징 분석 결과 비가전제품으로 판별",
                    "image_features": image_features
                }
                
        except Exception as e:
            logger.error(f"가전제품 판별 중 오류: {e}")
            # 오류 발생 시 기본적으로 가전제품으로 가정 (기존 동작 유지)
            return {
                "is_appliance": True,
                "confidence": 0.5,
                "reason": "판별 중 오류 발생으로 기본값 사용"
            }
    
    def _analyze_appliance_image_features(self, image_path: str) -> Dict[str, float]:
        """이미지 특징을 분석하여 가전제품 여부 판별"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {"appliance_score": 0.5, "non_appliance_score": 0.5}
            
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            height, width = image.shape[:2]
            
            appliance_score = 0.0
            non_appliance_score = 0.0
            
            # 가전제품 특징 분석
            # 1. 기하학적 형태 (직사각형, 원형 등)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 가장 큰 윤곽선 분석
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                if area > (height * width * 0.1):  # 충분히 큰 객체
                    # 직사각형 형태 검사
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    aspect_ratio = w / h if h > 0 else 0
                    if 0.5 <= aspect_ratio <= 2.0:  # 적절한 비율
                        appliance_score += 0.3
            
            # 2. 색상 분석 (가전제품은 주로 흰색, 회색, 검은색)
            white_mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
            gray_mask = cv2.inRange(hsv, np.array([0, 0, 50]), np.array([180, 50, 200]))
            black_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 50]))
            
            white_ratio = cv2.countNonZero(white_mask) / (height * width)
            gray_ratio = cv2.countNonZero(gray_mask) / (height * width)
            black_ratio = cv2.countNonZero(black_mask) / (height * width)
            
            neutral_color_ratio = white_ratio + gray_ratio + black_ratio
            if neutral_color_ratio > 0.3:  # 중성색이 30% 이상
                appliance_score += 0.4
            
            # 3. 텍스처 분석 (가전제품은 매끄러운 표면)
            # 간단한 텍스처 분석: 엣지 밀도
            edge_density = cv2.countNonZero(edges) / (height * width)
            if edge_density < 0.1:  # 엣지가 적음 (매끄러운 표면)
                appliance_score += 0.2
            
            # 비가전제품 특징 분석 (강화)
            # 1. 자연스러운 색상 (녹색, 파란색, 갈색, 주황색 등)
            green_mask = cv2.inRange(hsv, np.array([40, 40, 40]), np.array([80, 255, 255]))
            blue_mask = cv2.inRange(hsv, np.array([100, 40, 40]), np.array([130, 255, 255]))
            brown_mask = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([20, 255, 255]))
            orange_mask = cv2.inRange(hsv, np.array([5, 50, 50]), np.array([15, 255, 255]))
            
            green_ratio = cv2.countNonZero(green_mask) / (height * width)
            blue_ratio = cv2.countNonZero(blue_mask) / (height * width)
            brown_ratio = cv2.countNonZero(brown_mask) / (height * width)
            orange_ratio = cv2.countNonZero(orange_mask) / (height * width)
            
            natural_color_ratio = green_ratio + blue_ratio + brown_ratio + orange_ratio
            if natural_color_ratio > 0.15:  # 자연색이 15% 이상 (임계값 낮춤)
                non_appliance_score += 0.4
            
            # 2. 복잡한 텍스처 (털, 피부 등) - 더 민감하게
            if edge_density > 0.12:  # 엣지가 많음 (복잡한 텍스처) - 임계값 낮춤
                non_appliance_score += 0.4
            
            # 3. 유기적 형태 (동물, 사람 등) - 더 민감하게
            # 원형 형태 검사
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > (height * width * 0.03):  # 더 작은 객체도 검사
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        if circularity > 0.6:  # 원형에 가까움 (임계값 낮춤)
                            non_appliance_score += 0.3
                            break
            
            # 4. 동물 특징 검사 (강화)
            # 고양이, 강아지 등의 특징적인 색상 범위 (더 넓은 범위)
            animal_colors = [
                # 갈색 계열 (동물 털)
                cv2.inRange(hsv, np.array([5, 20, 20]), np.array([30, 255, 255])),
                # 회색 계열 (동물 털)
                cv2.inRange(hsv, np.array([0, 0, 30]), np.array([180, 50, 200])),
                # 흰색 계열 (동물 털)
                cv2.inRange(hsv, np.array([0, 0, 120]), np.array([180, 50, 255])),
                # 주황색 계열 (고양이 털)
                cv2.inRange(hsv, np.array([5, 50, 50]), np.array([20, 255, 255])),
                # 검은색 계열 (동물 털)
                cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 80]))
            ]
            
            animal_color_ratio = 0
            for mask in animal_colors:
                animal_color_ratio += cv2.countNonZero(mask) / (height * width)
            
            if animal_color_ratio > 0.15:  # 동물 색상이 15% 이상 (임계값 낮춤)
                non_appliance_score += 0.6
            
            # 5. 대비 분석 (동물은 대비가 높음)
            gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
            contrast = np.std(gray_blur)
            if contrast > 30:  # 대비가 높음
                non_appliance_score += 0.3
            
            return {
                "appliance_score": min(appliance_score, 1.0),
                "non_appliance_score": min(non_appliance_score, 1.0)
            }
            
        except Exception as e:
            logger.error(f"이미지 특징 분석 중 오류: {e}")
            return {"appliance_score": 0.5, "non_appliance_score": 0.5}
    
    def extract_text_from_image(self, image_path: str) -> List[Dict[str, Any]]:
        """이미지에서 텍스트 추출"""
        if not EASYOCR_AVAILABLE:
            logger.info("EasyOCR 없이 기본 분류 모드로 실행")
            return []
            
        self._initialize_ocr()
        
        if self.ocr_reader is None:
            logger.warning("OCR 리더가 초기화되지 않음 - 기본 분류 모드로 실행")
            return []
        
        try:
            # 이미지 읽기
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"이미지를 읽을 수 없음: {image_path}")
                return []
            
            # OCR 수행
            results = self.ocr_reader.readtext(image)
            
            # 결과 정리
            extracted_texts = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # 최소 신뢰도 필터링
                    extracted_texts.append({
                        'text': text.strip(),
                        'confidence': confidence,
                        'bbox': bbox
                    })
            
            logger.info(f"추출된 텍스트: {[item['text'] for item in extracted_texts]}")
            return extracted_texts
            
        except Exception as e:
            logger.error(f"OCR 처리 중 오류: {e}")
            logger.info("OCR 오류로 인해 기본 분류 모드로 전환")
            return []
    
    def detect_brand_from_text(self, extracted_texts: List[Dict[str, Any]]) -> Optional[str]:
        """추출된 텍스트에서 브랜드 검출"""
        brand_patterns = {
            "samsung": [r"samsung", r"삼성", r"galaxy", r"갤럭시", r"snMsuNG", r"snmsung", r"SM"],
            "lg": [r"lg", r"엘지", r"life'?s?\s*good", r"LG"],
            "philips": [r"philips", r"필립스", r"飛利浦", r"PHILIPS"],
            "cuckoo": [r"cuckoo", r"쿠쿠", r"뻐꾸기", r"CUCKOO"],
            "winix": [r"winix", r"위닉스", r"WINIX"],
            "xiaomi": [r"xiaomi", r"샤오미", r"mi", r"小米", r"XIAOMI"],
            "dyson": [r"dyson", r"다이슨", r"DYSON"],
            "sharp": [r"sharp", r"샤프", r"シャープ", r"SHARP"],
            "panasonic": [r"panasonic", r"파나소닉", r"パナソニック", r"PANASONIC"]
        }
        
        # 모든 추출된 텍스트를 하나의 문자열로 결합
        all_text = " ".join([item['text'].lower() for item in extracted_texts])
        
        # 브랜드별 패턴 매칭
        for brand, patterns in brand_patterns.items():
            for pattern in patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    logger.info(f"브랜드 검출: {brand} (패턴: {pattern})")
                    return brand
        
        logger.info("브랜드를 검출할 수 없음")
        return None
    
    async def classify_product_category(self, image_path: str, detected_brand: Optional[str] = None) -> Dict[str, Any]:
        """제품 카테고리 분류 (웹 검색 통합)"""
        try:
            # 1단계: 가전제품 여부 판별
            appliance_check = self.is_appliance_image(image_path)
            
            if not appliance_check["is_appliance"]:
                logger.warning(f"가전제품이 아닌 이미지로 판별됨: {appliance_check['reason']}")
                return {
                    "success": False,
                    "category": "가전제품_아님",
                    "brand": "해당없음",
                    "confidence": appliance_check["confidence"],
                    "message": f"가전제품이 아닙니다. {appliance_check['reason']} 가전제품 사진을 촬영해주세요.",
                    "appliance_check": appliance_check,
                    "extracted_texts": []
                }
            
            # 2단계: 가전제품인 경우 상세 분류 시작
            logger.info("가전제품으로 판별됨 - 상세 분류 시작")
            
            # 이미지에서 텍스트 추출
            extracted_texts = self.extract_text_from_image(image_path)
            all_text = " ".join([item['text'].lower() for item in extracted_texts])
            
            # 브랜드가 검출되지 않은 경우 OCR로 다시 시도
            if not detected_brand:
                detected_brand = self.detect_brand_from_text(extracted_texts)
            
            if detected_brand:
                logger.info(f"브랜드 검출: {detected_brand}")
                
                # 3단계: 기본 OCR 기반 분류
                basic_result = self._basic_classify_product(image_path, detected_brand, extracted_texts, all_text, appliance_check)
                
                if not basic_result["success"]:
                    return basic_result
                
                # 4단계: 간단한 제품 검색으로 모델명 찾기
                try:
                    logger.info(f"제품 검색 시작: {detected_brand} - {basic_result['category']}")
                    
                    # 먼저 이미지 기반 검색 시도
                    image_search_result = await simple_product_search_service.search_product_by_image(
                        image_path, 
                        detected_brand.lower(), 
                        basic_result["category"]
                    )
                    
                    if image_search_result["success"]:
                        # 이미지 기반 검색 결과 사용
                        product_info = image_search_result["product_info"]
                        
                        logger.info(f"이미지 기반 제품 검색 성공: {product_info['brand']} {product_info['model']}")
                        
                        return {
                            "success": True,
                            "category": product_info["category"],
                            "brand": product_info["brand"],
                            "model": product_info["model"],
                            "confidence": product_info["confidence"],
                            "message": f"이미지 분석으로 제품 정보를 찾았습니다: {product_info['brand']} {product_info['model']}",
                            "extracted_texts": product_info["extracted_texts"],
                            "appliance_check": appliance_check,
                            "search_method": "image_based_search",
                            "product_title": f"{product_info['brand']} {product_info['model']}",
                            "similarity_score": product_info["confidence"]
                        }
                    else:
                        # 이미지 기반 검색 실패 시 기존 검색 방법 사용
                        search_result = await simple_product_search_service.get_product_details(
                            detected_brand.lower(), 
                            basic_result["category"], 
                            image_path
                        )
                        
                        if search_result["success"]:
                            # 검색 결과로 업데이트
                            product_details = search_result["product_details"]
                            
                            logger.info(f"제품 검색 성공: {product_details['title']}")
                            
                            return {
                                "success": True,
                                "category": product_details["category"],
                                "brand": product_details["brand"],
                                "model": product_details.get("model", ""),
                                "confidence": product_details["confidence"],
                                "message": f"제품 정보를 찾았습니다: {product_details['title']}",
                                "extracted_texts": [item['text'] for item in extracted_texts],
                                "appliance_check": appliance_check,
                                "search_method": product_details["search_method"],
                                "product_title": product_details["title"],
                                "similarity_score": product_details["similarity"]
                            }
                        else:
                            logger.info(f"제품 검색 실패, 기본 분류 결과 사용: {search_result.get('error', '')}")
                            return basic_result
                        
                except Exception as e:
                    logger.warning(f"제품 검색 중 오류 발생, 기본 분류 결과 사용: {e}")
                    return basic_result
            else:
                # 브랜드가 검출되지 않은 경우 기본 분류
                return {
                    "success": True,
                    "category": "공기청정기",
                    "brand": "unknown",
                    "confidence": 0.6,
                    "message": "브랜드를 확인할 수 없어 기본 분류를 적용했습니다.",
                    "extracted_texts": [item['text'] for item in extracted_texts],
                    "appliance_check": appliance_check
                }
                
        except Exception as e:
            logger.error(f"제품 분류 중 오류: {e}")
            return {
                "success": False,
                "category": "오류",
                "brand": "불분명",
                "confidence": 0.0,
                "message": f"분류 중 오류가 발생했습니다: {str(e)}",
                "extracted_texts": []
            }
    
    def _basic_classify_product(self, image_path: str, detected_brand: str, extracted_texts: List[Dict], all_text: str, appliance_check: Dict) -> Dict[str, Any]:
        """기본 OCR 기반 제품 분류"""
        try:
            # 이미지 기반 특징 분석
            category_scores = self._analyze_image_features(image_path, all_text)
            
            # 브랜드가 검출된 경우 해당 브랜드 제품군으로 제한
            if detected_brand and detected_brand in self.brand_categories:
                available_categories = self.brand_categories[detected_brand]
                # 브랜드 제품군에 없는 카테고리는 점수를 낮춤
                for category in list(category_scores.keys()):
                    if category not in available_categories:
                        category_scores[category] *= 0.3
            
            # 최고 점수 카테고리 선택
            if category_scores:
                best_category = max(category_scores.items(), key=lambda x: x[1])
                confidence = best_category[1]
                
                # 확신도 임계값 검사
                if confidence < self.confidence_threshold:
                    return {
                        "success": False,
                        "category": "분류_불가",
                        "brand": detected_brand or "불분명",
                        "confidence": confidence,
                        "message": "확신도가 낮습니다. 제품의 브랜드명과 모델명이 명확히 보이도록 다시 촬영해주세요.",
                        "extracted_texts": [item['text'] for item in extracted_texts],
                        "appliance_check": appliance_check
                    }
                
                return {
                    "success": True,
                    "category": best_category[0],
                    "brand": detected_brand or "불분명",
                    "confidence": confidence,
                    "message": "제품이 성공적으로 분류되었습니다.",
                    "extracted_texts": [item['text'] for item in extracted_texts],
                    "appliance_check": appliance_check
                }
            
            return {
                "success": False,
                "category": "분류_불가",
                "brand": detected_brand or "불분명",
                "confidence": 0.0,
                "message": "제품 카테고리를 분류할 수 없습니다. 다시 촬영해주세요.",
                "extracted_texts": [item['text'] for item in extracted_texts],
                "appliance_check": appliance_check
            }
            
        except Exception as e:
            logger.error(f"기본 제품 분류 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "기본 제품 분류 중 오류가 발생했습니다."
            }
    
    def _analyze_image_features(self, image_path: str, text_content: str) -> Dict[str, float]:
        """이미지 특징 분석하여 카테고리별 점수 계산"""
        scores = {}
        
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                return scores
            
            # 이미지를 HSV로 변환
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            height, width = image.shape[:2]
            
            # 각 카테고리별 특징 분석
            for category, keywords in self.category_keywords.items():
                score = 0.0
                
                # 텍스트 기반 점수
                for keyword in keywords:
                    if keyword.lower() in text_content:
                        score += 0.3
                
                # 이미지 특징 기반 점수
                if category == "가습기":
                    # 가습기: 물탱크(투명/파란색), 원형/원통형 모양
                    blue_mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([130, 255, 255]))
                    blue_ratio = cv2.countNonZero(blue_mask) / (height * width)
                    score += blue_ratio * 2.0
                    
                elif category == "에어프라이어":
                    # 에어프라이어: 검은색 바스켓, 원형 모양
                    black_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 50]))
                    black_ratio = cv2.countNonZero(black_mask) / (height * width)
                    score += black_ratio * 1.5
                    
                elif category == "공기청정기":
                    # 공기청정기: 세로로 긴 형태, 흰색/회색
                    if height > width * 1.2:  # 세로가 더 긴 경우
                        score += 0.5
                    white_mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
                    white_ratio = cv2.countNonZero(white_mask) / (height * width)
                    score += white_ratio * 1.0
                
                # 기본 점수 (모든 카테고리에 최소 점수 부여)
                scores[category] = max(score, 0.1)
            
            return scores
            
        except Exception as e:
            logger.error(f"이미지 특징 분석 중 오류: {e}")
            return {category: 0.1 for category in self.category_keywords.keys()}


# 전역 서비스 인스턴스
product_recognition_service = ProductRecognitionService() 