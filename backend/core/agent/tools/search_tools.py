"""
MCP 검색 도구
"""

from typing import Dict, List, Any
from langchain_core.tools import tool
from utils.logger import logger


@tool
def naver_search(query: str, search_type: str = "webkr") -> Dict[str, Any]:
    """
    네이버 검색을 수행합니다.
    
    Args:
        query: 검색할 키워드
        search_type: 검색 유형 (webkr, news, blog, shop 등)
    
    Returns:
        검색 결과 딕셔너리
    """
    
    logger.info(f"네이버 검색 요청: {query} (타입: {search_type})")
    
    try:
        # 실제 구현에서는 MCP Naver Search 도구 사용
        # 현재는 임시 구현
        mock_results = {
            "success": True,
            "query": query,
            "search_type": search_type,
            "results": [
                {
                    "title": f"{query} 사용법 가이드",
                    "description": f"{query}의 기본 사용법과 주의사항을 상세히 설명합니다.",
                    "url": "https://example.com/guide1",
                    "date": "2024-01-15"
                },
                {
                    "title": f"{query} 매뉴얼 다운로드",
                    "description": f"공식 매뉴얼과 설명서를 제공합니다.",
                    "url": "https://example.com/manual",
                    "date": "2024-01-10"
                }
            ]
        }
        
        logger.info(f"네이버 검색 완료: {len(mock_results['results'])}개 결과")
        return mock_results
        
    except Exception as e:
        logger.error(f"네이버 검색 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@tool
def exa_search(query: str, search_type: str = "web") -> Dict[str, Any]:
    """
    Exa 검색을 수행합니다.
    
    Args:
        query: 검색할 키워드 (영어 권장)
        search_type: 검색 유형 (web, research, company 등)
    
    Returns:
        검색 결과 딕셔너리
    """
    
    logger.info(f"Exa 검색 요청: {query} (타입: {search_type})")
    
    try:
        # 실제 구현에서는 MCP Exa Search 도구 사용
        # 현재는 임시 구현
        mock_results = {
            "success": True,
            "query": query,
            "search_type": search_type,
            "results": [
                {
                    "title": f"{query} User Manual",
                    "description": f"Comprehensive user manual and troubleshooting guide for {query}.",
                    "url": "https://example.com/manual-en",
                    "content": f"This is a detailed guide for using {query} safely and efficiently...",
                    "date": "2024-01-20"
                },
                {
                    "title": f"{query} Reviews and Tips",
                    "description": f"User reviews and practical tips for {query}.",
                    "url": "https://example.com/reviews",
                    "content": f"Users share their experience with {query}...",
                    "date": "2024-01-18"
                }
            ]
        }
        
        logger.info(f"Exa 검색 완료: {len(mock_results['results'])}개 결과")
        return mock_results
        
    except Exception as e:
        logger.error(f"Exa 검색 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@tool
def search_product_manual(brand: str, model: str, category: str) -> Dict[str, Any]:
    """
    특정 제품의 매뉴얼을 검색합니다.
    
    Args:
        brand: 제품 브랜드
        model: 제품 모델
        category: 제품 카테고리
    
    Returns:
        매뉴얼 검색 결과
    """
    
    query_kr = f"{brand} {model} {category} 사용법 매뉴얼"
    query_en = f"{brand} {model} {category} manual guide"
    
    logger.info(f"제품 매뉴얼 검색: {query_kr}")
    
    try:
        # 네이버와 Exa 검색을 모두 수행
        naver_results = naver_search(query_kr, "webkr")
        exa_results = exa_search(query_en, "web")
        
        combined_results = {
            "success": True,
            "product": {
                "brand": brand,
                "model": model,
                "category": category
            },
            "naver_results": naver_results.get("results", []),
            "exa_results": exa_results.get("results", []),
            "total_results": len(naver_results.get("results", [])) + len(exa_results.get("results", []))
        }
        
        logger.info(f"제품 매뉴얼 검색 완료: 총 {combined_results['total_results']}개 결과")
        return combined_results
        
    except Exception as e:
        logger.error(f"제품 매뉴얼 검색 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "product": {"brand": brand, "model": model, "category": category},
            "results": []
        }


@tool
def search_troubleshooting(brand: str, model: str, problem: str) -> Dict[str, Any]:
    """
    제품 문제 해결 방법을 검색합니다.
    
    Args:
        brand: 제품 브랜드
        model: 제품 모델  
        problem: 문제 상황
    
    Returns:
        문제 해결 검색 결과
    """
    
    query_kr = f"{brand} {model} {problem} 해결방법 고장"
    query_en = f"{brand} {model} {problem} troubleshooting fix"
    
    logger.info(f"문제 해결 검색: {query_kr}")
    
    try:
        # 네이버와 Exa 검색 수행
        naver_results = naver_search(query_kr, "webkr")
        exa_results = exa_search(query_en, "web")
        
        combined_results = {
            "success": True,
            "problem": {
                "brand": brand,
                "model": model,
                "issue": problem
            },
            "solutions": naver_results.get("results", []) + exa_results.get("results", []),
            "total_solutions": len(naver_results.get("results", [])) + len(exa_results.get("results", []))
        }
        
        logger.info(f"문제 해결 검색 완료: 총 {combined_results['total_solutions']}개 해결책")
        return combined_results
        
    except Exception as e:
        logger.error(f"문제 해결 검색 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "problem": {"brand": brand, "model": model, "issue": problem},
            "solutions": []
        }


@tool
def naver_image_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    네이버 이미지 검색을 수행합니다.
    
    Args:
        query: 검색할 키워드
        max_results: 최대 검색 결과 수 (기본 10)
    
    Returns:
        이미지 검색 결과 딕셔너리
    """
    
    logger.info(f"네이버 이미지 검색 요청: {query}")
    
    try:
        # 실제 네이버 이미지 검색 API 호출
        import aiohttp
        import os
        
        client_id = os.getenv("NAVER_CLIENT_ID")
        client_secret = os.getenv("NAVER_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            logger.warning("네이버 API 키가 설정되지 않음")
            return {
                "success": False,
                "error": "네이버 API 키가 설정되지 않았습니다.",
                "results": []
            }
        
        url = "https://openapi.naver.com/v1/search/image"
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        params = {
            "query": query,
            "display": min(max_results, 10),
            "start": 1,
            "sort": "sim"
        }
        
        # 동기 HTTP 요청 (MCP 도구에서는 비동기 사용 불가)
        import requests
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("items", [])
            
            logger.info(f"네이버 이미지 검색 완료: {len(results)}개 결과")
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_count": data.get("total", 0)
            }
        else:
            logger.error(f"네이버 이미지 검색 API 오류: {response.status_code}")
            return {
                "success": False,
                "error": f"API 오류: {response.status_code}",
                "results": []
            }
            
    except Exception as e:
        logger.error(f"네이버 이미지 검색 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


@tool
def naver_web_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    네이버 웹 검색을 수행합니다.
    
    Args:
        query: 검색할 키워드
        max_results: 최대 검색 결과 수 (기본 10)
    
    Returns:
        웹 검색 결과 딕셔너리
    """
    
    logger.info(f"네이버 웹 검색 요청: {query}")
    
    try:
        # 실제 네이버 웹 검색 API 호출
        import requests
        import os
        
        client_id = os.getenv("NAVER_CLIENT_ID")
        client_secret = os.getenv("NAVER_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            logger.warning("네이버 API 키가 설정되지 않음")
            return {
                "success": False,
                "error": "네이버 API 키가 설정되지 않았습니다.",
                "results": []
            }
        
        url = "https://openapi.naver.com/v1/search/webkr"
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }
        params = {
            "query": query,
            "display": min(max_results, 10),
            "start": 1,
            "sort": "sim"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("items", [])
            
            logger.info(f"네이버 웹 검색 완료: {len(results)}개 결과")
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_count": data.get("total", 0)
            }
        else:
            logger.error(f"네이버 웹 검색 API 오류: {response.status_code}")
            return {
                "success": False,
                "error": f"API 오류: {response.status_code}",
                "results": []
            }
            
    except Exception as e:
        logger.error(f"네이버 웹 검색 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


# 사용 가능한 모든 도구 리스트
AVAILABLE_TOOLS = [
    naver_search,
    naver_image_search,
    naver_web_search
] 