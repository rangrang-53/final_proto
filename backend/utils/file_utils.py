"""
파일 처리 유틸리티
"""

import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io

from config.settings import settings
from utils.logger import logger


def validate_image_file(file: UploadFile) -> Tuple[bool, str]:
    """이미지 파일 검증"""
    
    # 파일명 검증
    if not file.filename:
        return False, "파일명이 없습니다."
    
    # 파일 확장자 검증
    file_extension = file.filename.split(".")[-1].lower()
    allowed_extensions = settings.allowed_extensions.split(",")
    if file_extension not in allowed_extensions:
        return False, f"지원하지 않는 파일 형식입니다. ({', '.join(allowed_extensions)}만 지원)"
    
    # 파일 크기 검증 (file.size가 None일 수 있음)
    if file.size is not None and file.size > settings.max_file_size:
        return False, f"파일 크기가 {settings.max_file_size // (1024*1024)}MB를 초과합니다."
    
    # 파일이 비어있는지 확인
    if file.size is not None and file.size == 0:
        return False, "파일이 비어있습니다."
    
    return True, "유효한 파일입니다."


def create_upload_directory():
    """업로드 디렉토리 생성"""
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


async def save_uploaded_file(file: UploadFile, session_id: str) -> Tuple[str, str]:
    """업로드된 파일 저장"""
    
    try:
        # 업로드 디렉토리 생성
        upload_dir = create_upload_directory()
        
        # 고유한 파일명 생성
        file_extension = file.filename.split(".")[-1].lower()
        unique_filename = f"{session_id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = upload_dir / unique_filename
        
        # 파일 포인터를 처음으로 이동
        await file.seek(0)
        
        # 파일 저장
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"파일 저장 완료: {file_path}")
        
        return str(file_path), unique_filename
        
    except Exception as e:
        logger.error(f"파일 저장 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 저장 중 오류가 발생했습니다."
        )


def validate_and_process_image(file_path: str) -> Tuple[bool, Optional[dict]]:
    """이미지 검증 및 기본 정보 추출 (개선된 전처리)"""
    
    try:
        # 파일 존재 확인
        if not os.path.exists(file_path):
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            return False, None
            
        # 파일 크기 확인
        if os.path.getsize(file_path) == 0:
            logger.error(f"파일이 비어있습니다: {file_path}")
            return False, None
        
        with Image.open(file_path) as img:
            # 이미지를 실제로 로드해서 검증
            img.load()
            
            # 원본 이미지 정보
            original_info = {
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height
            }
            
            # 이미지가 너무 작은 경우 검증 (최소 크기를 더 관대하게 설정)
            if img.width < 100 or img.height < 100:
                logger.error(f"이미지가 너무 작습니다: {img.width}x{img.height}")
                return False, None
            
            # 이미지 품질 개선 처리
            processed_img = _enhance_image_for_ocr(img)
            
            # 처리된 이미지 저장 (원본 덮어쓰기)
            if processed_img != img:
                processed_img.save(file_path, quality=95, optimize=True)
                logger.info(f"이미지 전처리 완료: {file_path}")
            
            # 최종 이미지 정보
            image_info = {
                "format": processed_img.format or img.format,
                "mode": processed_img.mode,
                "size": processed_img.size,
                "width": processed_img.width,
                "height": processed_img.height,
                "original_size": original_info["size"],
                "processed": processed_img != img
            }
            
            logger.info(f"이미지 정보: {image_info}")
            return True, image_info
            
    except Exception as e:
        logger.error(f"이미지 처리 실패: {str(e)}")
        return False, None


def _enhance_image_for_ocr(img: Image.Image) -> Image.Image:
    """OCR 성능 향상을 위한 이미지 개선"""
    try:
        # RGB 모드로 변환
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 이미지 크기가 너무 작으면 확대 (로고/텍스트 가독성 향상)
        width, height = img.size
        if width < 800 or height < 600:
            # 비율을 유지하면서 최소 800x600으로 확대
            scale_factor = max(800 / width, 600 / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"이미지 크기 확대: {width}x{height} → {new_width}x{new_height}")
        
        # 이미지가 너무 크면 축소 (처리 속도 향상)
        elif width > 2000 or height > 2000:
            # 최대 2000픽셀로 제한
            scale_factor = min(2000 / width, 2000 / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"이미지 크기 축소: {width}x{height} → {new_width}x{new_height}")
        
        # 밝기와 대비 조정 (텍스트 가독성 향상)
        from PIL import ImageEnhance
        
        # 대비 약간 증가
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        # 선명도 약간 증가
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        return img
        
    except Exception as e:
        logger.error(f"이미지 개선 중 오류: {e}")
        return img  # 오류 시 원본 반환


def cleanup_temp_file(file_path: str):
    """임시 파일 정리"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"임시 파일 삭제: {file_path}")
    except Exception as e:
        logger.error(f"파일 삭제 실패: {str(e)}")


def get_file_info(file_path: str) -> dict:
    """파일 정보 조회"""
    try:
        file_stat = os.stat(file_path)
        return {
            "size": file_stat.st_size,
            "created_at": file_stat.st_ctime,
            "modified_at": file_stat.st_mtime
        }
    except Exception as e:
        logger.error(f"파일 정보 조회 실패: {str(e)}")
        return {} 