"""
메모리 기반 데이터베이스 설정
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading
from config.settings import settings


class MemoryDatabase:
    """메모리 기반 데이터베이스"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def create_session(self, session_id: str) -> Dict[str, Any]:
        """세션 생성"""
        with self._lock:
            expires_at = datetime.now() + timedelta(hours=settings.session_expire_hours)
            session_data = {
                "session_id": session_id,
                "created_at": datetime.now(),
                "expires_at": expires_at,
                "product_info": None,
                "chat_history": [],
                "temp_files": []
            }
            self._sessions[session_id] = session_data
            return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 조회"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session["expires_at"] > datetime.now():
                return session
            elif session:
                # 만료된 세션 삭제
                del self._sessions[session_id]
            return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """세션 업데이트"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session["expires_at"] > datetime.now():
                session.update(data)
                return True
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        with self._lock:
            now = datetime.now()
            expired_sessions = [
                sid for sid, session in self._sessions.items()
                if session["expires_at"] <= now
            ]
            for sid in expired_sessions:
                del self._sessions[sid]
            return len(expired_sessions)
    
    def get_session_count(self) -> int:
        """활성 세션 수 조회"""
        with self._lock:
            return len(self._sessions)


# 전역 데이터베이스 인스턴스
memory_db = MemoryDatabase() 