"""
로깅 설정
"""

import logging
import sys
import os
from pathlib import Path
from config.settings import settings

# 시스템 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'


def setup_logger(name: str = "app") -> logging.Logger:
    """로거 설정"""
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 이미 핸들러가 있으면 중복 생성 방지
    if logger.handlers:
        return logger
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (로그 디렉토리가 있을 경우)
    log_dir = Path("logs")
    if log_dir.exists() or log_dir.mkdir(exist_ok=True):
        file_handler = logging.FileHandler(log_dir / f"{name}.log", encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 전역 로거 인스턴스
logger = setup_logger() 