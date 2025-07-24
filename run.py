#!/usr/bin/env python3
"""
5060 중장년층 가전제품 사용법 안내 Agent 실행 스크립트
"""

import subprocess
import sys
import os
import time
from pathlib import Path

# 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_backend():
    """백엔드 서버 실행"""
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    print("🚀 백엔드 서버를 시작합니다...")
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--reload", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ], env=env)

def run_frontend():
    """프론트엔드 서버 실행"""
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    print("🎨 프론트엔드 서버를 시작합니다...")
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    subprocess.run([
        sys.executable, "-m", "streamlit", 
        "run", "app.py", 
        "--server.port", "8501"
    ], env=env)

def main():
    """메인 실행 함수"""
    if len(sys.argv) < 2:
        print("사용법: python run.py [backend|frontend|both]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "backend":
        run_backend()
    elif command == "frontend":
        run_frontend()
    elif command == "both":
        print("🔄 백엔드와 프론트엔드를 모두 실행합니다...")
        print("백엔드를 먼저 실행한 후, 별도 터미널에서 프론트엔드를 실행하세요.")
        run_backend()
    else:
        print("❌ 잘못된 명령어입니다. [backend|frontend|both] 중 하나를 선택하세요.")
        sys.exit(1)

if __name__ == "__main__":
    main() 