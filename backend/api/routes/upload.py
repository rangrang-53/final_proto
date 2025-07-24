"""
이미지 업로드 API
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from datetime import datetime
import uuid
from typing import Optional

from api.dependencies import get_database, get_logger
from config.database import MemoryDatabase
from utils.file_utils import (
    validate_image_file, save_uploaded_file, 
    validate_and_process_image, cleanup_temp_file
)
from services.product_recognition_service import product_recognition_service


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """이미지 파일 업로드"""
    
    logger.info(f"이미지 업로드 요청: {file.filename}")
    
    try:
        # 파일 검증
        is_valid, message = validate_image_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # 세션 ID 처리
        if session_id:
            # 기존 세션 사용
            session_data = db.get_session(session_id)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="세션을 찾을 수 없습니다."
                )
        else:
            # 새 세션 생성
            session_id = str(uuid.uuid4())
            session_data = db.create_session(session_id)
        
        # 파일 저장
        file_path, filename = await save_uploaded_file(file, session_id)
        
        # 이미지 검증 및 정보 추출
        is_valid_image, image_info = validate_and_process_image(file_path)
        if not is_valid_image:
            cleanup_temp_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 이미지 파일입니다."
            )
        
        # 제품 인식 수행
        logger.info("제품 인식 시작...")
        recognition_result = await product_recognition_service.classify_product_category(file_path)
        
        # 세션에 파일 정보 및 인식 결과 저장
        session_update_data = {
            "temp_files": [file_path],
            "uploaded_image": {
                "filename": filename,
                "original_name": file.filename,
                "file_path": file_path,
                "image_info": image_info,
                "uploaded_at": datetime.now().isoformat()
            },
            "product_recognition": recognition_result
        }
        
        db.update_session(session_id, session_update_data)
        
        logger.info(f"이미지 업로드 및 제품 인식 완료: {filename}")
        logger.info(f"인식 결과: {recognition_result}")
        
        # 응답 데이터 구성
        response_data = {
            "session_id": session_id,
            "filename": filename,
            "image_info": image_info,
            "product_recognition": recognition_result
        }
        
        # 인식 성공 여부에 따른 메시지 설정
        if recognition_result.get("success", False):
            response_data["message"] = f"이미지 업로드 및 제품 인식 완료: {recognition_result['brand']} {recognition_result['category']}"
        elif recognition_result.get("category") == "가전제품_아님":
            response_data["message"] = recognition_result.get('message', '가전제품이 아닙니다.')
        else:
            response_data["message"] = f"이미지 업로드 완료. {recognition_result.get('message', '제품 인식에 실패했습니다.')}"
        
        return {
            "success": True,
            "data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException as e:
        logger.error(f"이미지 업로드 HTTP 오류: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"이미지 업로드 실패: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이미지 업로드 중 오류가 발생했습니다."
        )


@router.get("/status/{session_id}")
async def get_upload_status(
    session_id: str,
    db: MemoryDatabase = Depends(get_database),
    logger = Depends(get_logger)
):
    """업로드 상태 조회"""
    
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )
    
    uploaded_image = session.get("uploaded_image")
    if not uploaded_image:
        return {
            "success": True,
            "data": {
                "status": "no_image",
                "message": "업로드된 이미지가 없습니다."
            },
            "timestamp": datetime.now().isoformat()
        }
    
    return {
        "success": True,
        "data": {
            "status": "uploaded",
            "filename": uploaded_image["filename"],
            "uploaded_at": uploaded_image["uploaded_at"],
            "image_info": uploaded_image["image_info"]
        },
        "timestamp": datetime.now().isoformat()
    } 