"""
제품 인식 API
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from datetime import datetime

from api.dependencies import get_database, get_logger, validate_session
from config.database import MemoryDatabase
from services.product_service import get_product_service
from models.request_models import ProductAnalysisResponse


router = APIRouter(prefix="/product", tags=["product"])


@router.post("/analyze/{session_id}")
async def analyze_product(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """제품 이미지 분석"""
    
    logger.info(f"제품 분석 요청: session_id={session_id}")
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    # 업로드된 이미지 확인
    if "uploaded_image" not in session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="분석할 이미지가 업로드되지 않았습니다."
        )
    
    try:
        # 제품 인식 서비스 호출
        product_service = get_product_service()
        
        # 백그라운드에서 분석 수행 (비동기)
        async def analyze_in_background():
            result = await product_service.analyze_product(session_id)
            logger.info(f"백그라운드 분석 완료: {result.get('success', False)}")
        
        background_tasks.add_task(analyze_in_background)
        
        # 즉시 응답 반환 (분석 진행 중 상태)
        return {
            "success": True,
            "data": {
                "status": "analyzing",
                "session_id": session_id,
                "message": "제품 분석이 시작되었습니다. 잠시 후 결과를 확인해 주세요.",
                "estimated_time": "30-60초"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"제품 분석 요청 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="제품 분석 요청 처리 중 오류가 발생했습니다."
        )


@router.get("/analyze/{session_id}/result")
async def get_analysis_result(
    session_id: str,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """제품 분석 결과 조회"""
    
    logger.info(f"분석 결과 조회: session_id={session_id}")
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    try:
        product_service = get_product_service()
        result = product_service.get_analysis_result(session_id)
        
        if result["success"]:
            return result
        else:
            # 분석이 아직 완료되지 않은 경우
            if "분석된 제품 정보가 없습니다" in result.get("error", ""):
                return {
                    "success": True,
                    "data": {
                        "status": "analyzing",
                        "message": "분석이 진행 중입니다. 잠시 후 다시 시도해 주세요."
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["error"]
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 결과 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="분석 결과 조회 중 오류가 발생했습니다."
        )


@router.post("/analyze/{session_id}/retry")
async def reanalyze_product(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """제품 재분석"""
    
    logger.info(f"제품 재분석 요청: session_id={session_id}")
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    try:
        product_service = get_product_service()
        
        # 백그라운드에서 재분석 수행
        async def reanalyze_in_background():
            result = await product_service.reanalyze_product(session_id)
            logger.info(f"백그라운드 재분석 완료: {result.get('success', False)}")
        
        background_tasks.add_task(reanalyze_in_background)
        
        return {
            "success": True,
            "data": {
                "status": "reanalyzing",
                "session_id": session_id,
                "message": "제품 재분석이 시작되었습니다.",
                "estimated_time": "30-60초"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"제품 재분석 요청 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="제품 재분석 요청 처리 중 오류가 발생했습니다."
        )


@router.get("/categories")
async def get_supported_categories(
    logger = Depends(get_logger)
):
    """지원되는 제품 카테고리 목록 조회"""
    
    logger.info("지원 제품 카테고리 조회")
    
    try:
        product_service = get_product_service()
        result = product_service.get_supported_categories()
        
        return result
        
    except Exception as e:
        logger.error(f"제품 카테고리 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="제품 카테고리 조회 중 오류가 발생했습니다."
        )


@router.get("/status/{session_id}")
async def get_product_status(
    session_id: str,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """제품 분석 상태 확인"""
    
    # 세션 유효성 검사
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    # 상태 정보 구성
    has_image = "uploaded_image" in session
    has_product_info = session.get("product_info") is not None
    has_usage_guide = session.get("usage_guide") is not None
    
    # 가전제품이 아닌 경우 확인
    product_info = session.get("product_info", {})
    is_non_appliance = product_info.get("category") == "가전제품_아님"
    
    if has_product_info:
        if is_non_appliance:
            status = "completed"
            message = "가전제품이 아닌 이미지로 판별되었습니다."
        else:
            status = "completed"
            message = "제품 분석이 완료되었습니다."
    elif has_image:
        status = "analyzing"
        message = "제품 분석이 진행 중입니다."
    else:
        status = "waiting"
        message = "이미지 업로드를 기다리고 있습니다."
    
    return {
        "success": True,
        "data": {
            "status": status,
            "message": message,
            "has_image": has_image,
            "has_product_info": has_product_info,
            "has_usage_guide": has_usage_guide,
            "session_id": session_id
        },
        "timestamp": datetime.now().isoformat()
    } 