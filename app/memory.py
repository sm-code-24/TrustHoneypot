"""
In-memory session storage for multi-turn conversations
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Stale sessions older than this are eligible for cleanup
SESSION_TTL_HOURS = 24
MAX_SESSIONS = 10000


class SessionMemory:
    """
    Keeps track of all conversations happening with different scammers.
    
    Like a notebook where we write down:
    - Who said what and when
    - How long we've been talking
    - Whether we've confirmed it's a scam
    - What information we've collected
    
    Each conversation has a unique session ID (like a conversation thread)
    """
    
    def __init__(self):
        # Dictionary to store all ongoing conversations
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self, session_id: str) -> None:
        """
        Initialize a new session
        
        Args:
            session_id: Unique session identifier
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "startTime": datetime.utcnow(),
                "messages": [],
                "messageCount": 0,
                "scamConfirmed": False,
                "callbackSent": False,
                "agentResponse": None,
            }
    
    def add_message(self, session_id: str, sender: str, text: str) -> None:
        """
        Add a message to session history
        
        Args:
            session_id: Session identifier
            sender: Message sender (scammer or agent)
            text: Message text
        """
        self.create_session(session_id)
        
        self.sessions[session_id]["messages"].append({
            "sender": sender,
            "text": text,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if sender == "scammer":
            self.sessions[session_id]["messageCount"] += 1
    
    def get_message_count(self, session_id: str) -> int:
        """Get total scammer messages for session"""
        if session_id not in self.sessions:
            return 0
        return self.sessions[session_id]["messageCount"]
    
    def get_duration(self, session_id: str) -> int:
        """
        Get engagement duration in seconds
        
        Args:
            session_id: Session identifier
            
        Returns:
            Duration in seconds
        """
        if session_id not in self.sessions:
            return 0
        
        start_time = self.sessions[session_id]["startTime"]
        duration = (datetime.utcnow() - start_time).total_seconds()
        return int(duration)
    
    def mark_scam_confirmed(self, session_id: str) -> None:
        """Mark that scam has been confirmed for session"""
        if session_id in self.sessions:
            self.sessions[session_id]["scamConfirmed"] = True
    
    def is_scam_confirmed(self, session_id: str) -> bool:
        """Check if scam is confirmed for session"""
        if session_id not in self.sessions:
            return False
        return self.sessions[session_id]["scamConfirmed"]
    
    def mark_callback_sent(self, session_id: str) -> None:
        """Mark that final callback has been sent"""
        if session_id in self.sessions:
            self.sessions[session_id]["callbackSent"] = True
    
    def is_callback_sent(self, session_id: str) -> bool:
        """Check if callback has been sent for session"""
        if session_id not in self.sessions:
            return False
        return self.sessions[session_id]["callbackSent"]
    
    def set_agent_response(self, session_id: str, response: str) -> None:
        """Store agent response for current turn"""
        if session_id in self.sessions:
            self.sessions[session_id]["agentResponse"] = response
    
    def get_agent_response(self, session_id: str) -> Optional[str]:
        """Get agent response for current turn"""
        if session_id not in self.sessions:
            return None
        return self.sessions[session_id].get("agentResponse")
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return session_id in self.sessions
    
    def cleanup_stale_sessions(self) -> int:
        """Remove sessions older than SESSION_TTL_HOURS. Returns count removed."""
        cutoff = datetime.utcnow() - timedelta(hours=SESSION_TTL_HOURS)
        stale = [
            sid for sid, data in self.sessions.items()
            if data["startTime"] < cutoff
        ]
        for sid in stale:
            del self.sessions[sid]
        return len(stale)
    
    def enforce_limit(self) -> None:
        """If over MAX_SESSIONS, drop the oldest sessions."""
        if len(self.sessions) <= MAX_SESSIONS:
            return
        # Sort by startTime, drop oldest
        sorted_ids = sorted(
            self.sessions.keys(),
            key=lambda sid: self.sessions[sid]["startTime"]
        )
        to_remove = sorted_ids[: len(self.sessions) - MAX_SESSIONS]
        for sid in to_remove:
            del self.sessions[sid]


# Global memory instance
memory = SessionMemory()
