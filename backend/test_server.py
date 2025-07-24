"""
간단한 테스트 FastAPI 서버
"""

import os
import sys

# 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Test Backend API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Backend server is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Test backend is working"}

if __name__ == "__main__":
    print("🚀 테스트 백엔드 서버를 시작합니다...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 