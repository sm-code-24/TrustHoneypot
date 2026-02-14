"""
MongoDB persistence for session summaries and learning.

PRIVACY: We store ONLY session summaries, NOT raw chat messages.
No OTPs, credentials, or personal identities are persisted.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from pymongo import MongoClient, DESCENDING
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    logger.warning("pymongo not installed. MongoDB features disabled.")


class DatabaseService:
    """MongoDB persistence for session intelligence summaries."""
    
    def __init__(self):
        self.mongo_uri = os.getenv("MONGODB_URI", "")
        self.db_name = os.getenv("MONGODB_DB", "trusthoneypot")
        self.client = None
        self.db = None
        self.enabled = False
        self._connect()
    
    def _connect(self):
        logger.info(f"DB INIT: pymongo={PYMONGO_AVAILABLE}, uri_set={bool(self.mongo_uri)}, uri_len={len(self.mongo_uri)}, db={self.db_name}")
        if not PYMONGO_AVAILABLE:
            logger.warning("DB service DISABLED: pymongo not installed.")
            return
        if not self.mongo_uri:
            logger.warning("DB service DISABLED: MONGODB_URI not set")
            return
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=3000)
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.enabled = True
            self._ensure_indexes()
            logger.info(f"DB CONNECTED: {self.db_name} — ready to store sessions & callbacks")
        except Exception as e:
            logger.error(f"DB CONNECTION FAILED: {e}", exc_info=True)
            self.enabled = False
    
    def _ensure_indexes(self):
        """Create indexes for all collections."""
        if not self.enabled or self.db is None:
            return
        try:
            self.db.session_summaries.create_index("sessionId", unique=True)
            self.db.session_summaries.create_index("timestamp")
            self.db.callback_records.create_index("sessionId", unique=True)
            self.db.intelligence_registry.create_index("value", unique=True)
            self.db.intelligence_registry.create_index("type")
            self.db.intelligence_registry.create_index("riskLevel")
            self.db.intelligence_registry.create_index("lastSeen")
            self.db.pattern_registry.create_index("sessionId", unique=True)
            self.db.pattern_registry.create_index("patternHash")
            self.db.pattern_registry.create_index("timestamp")
        except Exception as e:
            logger.warning(f"Index creation warning (non-fatal): {e}")
    
    # ── Session Summaries ──────────────────────────────────────────────
    
    def save_session_summary(
        self,
        session_id: str,
        scam_type: str,
        risk_level: str,
        confidence: float,
        message_count: int,
        scam_detected: bool,
        intelligence_counts: Dict[str, int],
        tactics: List[str],
        response_mode: str = "rule_based",
        callback_sent: bool = False,
        intelligence: dict = None,
    ):
        """Persist a session summary with intelligence data."""
        if not self.enabled:
            logger.warning(f"DB not enabled: callback record for session {session_id} not saved.")
            return
        try:
            doc = {
                "sessionId": session_id,
                "scamType": scam_type,
                "riskLevel": risk_level,
                "confidence": confidence,
                "messageCount": message_count,
                "scamDetected": scam_detected,
                "intelligenceTypes": intelligence_counts,
                "tactics": tactics,
                "responseMode": response_mode,
                "callbackSent": callback_sent,
                "timestamp": datetime.now(timezone.utc),
            }
            # Store actual intelligence items for UI display
            if intelligence:
                doc["intelligence"] = {
                    "bankAccounts": intelligence.get("bankAccounts", []),
                    "upiIds": intelligence.get("upiIds", []),
                    "phishingLinks": intelligence.get("phishingLinks", []),
                    "phoneNumbers": intelligence.get("phoneNumbers", []),
                    "suspiciousKeywords": intelligence.get("suspiciousKeywords", []),
                    "emails": intelligence.get("emails", []),
                }
            self.db.session_summaries.update_one(
                {"sessionId": session_id},
                {"$set": doc},
                upsert=True
            )
            logger.info(f"Session summary saved: {session_id[:8]}")
        except Exception as e:
            logger.error(f"Failed to save session summary: {e}")
    
    def get_session_summaries(self, limit: int = 50) -> List[dict]:
        """Get recent session summaries for UI."""
        if not self.enabled:
            return []
        try:
            cursor = self.db.session_summaries.find(
                {},
                {"_id": 0}
            ).sort("timestamp", DESCENDING).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to fetch session summaries: {e}")
            return []
    
    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """Get a single session summary."""
        if not self.enabled:
            return None
        try:
            return self.db.session_summaries.find_one(
                {"sessionId": session_id},
                {"_id": 0}
            )
        except Exception as e:
            logger.error(f"Failed to fetch session: {e}")
            return None
    
    # ── Callback Records ───────────────────────────────────────────────
    
    def save_callback_record(
        self,
        session_id: str,
        status: str,
        payload_summary: dict,
        intelligence: dict = None,
    ):
        """Save callback record with full intelligence data."""
        logger.info(f"SAVE CALLBACK RECORD: session={session_id[:8]}, status={status}, enabled={self.enabled}")
        if not self.enabled:
            logger.warning(f"DB NOT ENABLED: callback record for session {session_id[:8]} NOT saved")
            return
        try:
            doc = {
                "sessionId": session_id,
                "status": status,
                "payloadSummary": payload_summary,
                "timestamp": datetime.now(timezone.utc),
            }
            # Store actual intelligence items for UI highlighting
            if intelligence:
                doc["intelligence"] = {
                    "bankAccounts": intelligence.get("bankAccounts", []),
                    "upiIds": intelligence.get("upiIds", []),
                    "phishingLinks": intelligence.get("phishingLinks", []),
                    "phoneNumbers": intelligence.get("phoneNumbers", []),
                    "suspiciousKeywords": intelligence.get("suspiciousKeywords", []),
                    "emails": intelligence.get("emails", []),
                }
            self.db.callback_records.update_one(
                {"sessionId": session_id},
                {"$set": doc},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Failed to save callback record: {e}")
    
    def get_callback_records(self, limit: int = 50) -> List[dict]:
        """Get callback records for UI."""
        if not self.enabled:
            return []
        try:
            cursor = self.db.callback_records.find(
                {},
                {"_id": 0}
            ).sort("timestamp", DESCENDING).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to fetch callbacks: {e}")
            return []
    
    # ── Patterns / Learning ────────────────────────────────────────────
    
    def get_patterns(self) -> dict:
        """Aggregate scam patterns from stored session summaries."""
        if not self.enabled:
            return self._empty_patterns()
        try:
            pipeline_type = [
                {"$match": {"scamDetected": True}},
                {"$group": {"_id": "$scamType", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            pipeline_risk = [
                {"$match": {"scamDetected": True}},
                {"$group": {"_id": "$riskLevel", "count": {"$sum": 1}}}
            ]
            pipeline_tactics = [
                {"$match": {"scamDetected": True}},
                {"$unwind": "$tactics"},
                {"$group": {"_id": "$tactics", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            pipeline_stats = [
                {"$match": {"scamDetected": True}},
                {"$group": {
                    "_id": None,
                    "totalSessions": {"$sum": 1},
                    "avgMessages": {"$avg": "$messageCount"},
                    "avgConfidence": {"$avg": "$confidence"},
                    "callbacksSent": {"$sum": {"$cond": ["$callbackSent", 1, 0]}}
                }}
            ]
            
            type_dist = list(self.db.session_summaries.aggregate(pipeline_type))
            risk_dist = list(self.db.session_summaries.aggregate(pipeline_risk))
            top_tactics = list(self.db.session_summaries.aggregate(pipeline_tactics))
            stats = list(self.db.session_summaries.aggregate(pipeline_stats))
            
            return {
                "scam_types": type_dist,
                "risk_distribution": risk_dist,
                "top_tactics": top_tactics,
                "stats": stats[0] if stats else {},
            }
        except Exception as e:
            logger.error(f"Failed to compute patterns: {e}")
            return self._empty_patterns()
    
    def _empty_patterns(self) -> dict:
        return {
            "scam_types": [],
            "risk_distribution": [],
            "top_tactics": [],
            "stats": {},
        }
    
    def get_status(self) -> dict:
        return {
            "connected": self.enabled,
            "database": self.db_name if self.enabled else None,
            "pymongo_installed": PYMONGO_AVAILABLE,
            "uri_set": bool(self.mongo_uri)
        }


# Singleton
db_service = DatabaseService()
