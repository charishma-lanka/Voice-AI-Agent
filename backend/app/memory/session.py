import json
import time
from typing import Dict, Any, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class SessionMemory:
    """Session memory using Redis with TTL"""
    
    def __init__(self, redis_url: str = None, ttl_seconds: int = 1800):
        self.ttl_seconds = ttl_seconds
        self.redis_client = None
        self.local_storage = {}  # Fallback when Redis is not available
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                print("✅ Redis connected successfully")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}, using in-memory storage")
                self.redis_client = None
    
    async def get(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        start_time = time.time()
        
        if self.redis_client:
            data = self.redis_client.get(f"session:{session_id}")
            if data:
                latency = (time.time() - start_time) * 1000
                return {
                    "context": json.loads(data),
                    "latency_ms": round(latency, 2)
                }
        
        # Fallback to in-memory
        data = self.local_storage.get(session_id, {})
        latency = (time.time() - start_time) * 1000
        return {
            "context": data,
            "latency_ms": round(latency, 2)
        }
    
    async def set(self, session_id: str, context: Dict[str, Any]) -> None:
        """Set session context with TTL"""
        if self.redis_client:
            self.redis_client.setex(
                f"session:{session_id}",
                self.ttl_seconds,
                json.dumps(context)
            )
        else:
            self.local_storage[session_id] = context
    
    async def update(self, session_id: str, updates: Dict[str, Any]) -> None:
        """Update specific fields in session"""
        current = await self.get(session_id)
        current_context = current["context"]
        current_context.update(updates)
        await self.set(session_id, current_context)
    
    async def delete(self, session_id: str) -> None:
        """Delete session"""
        if self.redis_client:
            self.redis_client.delete(f"session:{session_id}")
        else:
            self.local_storage.pop(session_id, None)
    
    async def refresh_ttl(self, session_id: str) -> None:
        """Refresh TTL on existing session"""
        if self.redis_client:
            self.redis_client.expire(f"session:{session_id}", self.ttl_seconds)