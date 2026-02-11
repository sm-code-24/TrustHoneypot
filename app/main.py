"""
Agentic Honey-Pot API
Built for the India AI Impact Buildathon (GUVI) - Problem Statement 2

This is the main entry point for the honeypot system. It receives suspected
scam messages from the GUVI platform, analyzes them, generates responses,
extracts intelligence, and reports back when we've gathered enough info.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root (parent of app/) or current dir
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import time

from models import (
    HoneypotRequest,
    HoneypotResponse
)
from auth import verify_api_key
from detector import detector
from extractor import extractor
from agent import agent
from memory import memory
from callback import send_final_callback, should_send_callback
from llm import llm_service
from db import db_service

# Set up logging so we can see what's happening
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="Agentic Honey-Pot API",
    description="Scam Detection & Intelligence Extraction for GUVI Hackathon",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url=None,
)

# CORS — restrict in production, wide open in dev
_allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Production Middleware ────────────────────────────────────────────────────

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Add X-Process-Time header and log request timing."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{elapsed_ms:.0f}ms"
    if elapsed_ms > 2000:
        logger.warning(f"SLOW {request.method} {request.url.path} {elapsed_ms:.0f}ms")
    return response


# ─── Simple in-memory rate limiter ────────────────────────────────────────────

_rate_store: dict = {}  # ip -> (count, window_start)
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Basic per-IP rate limiting for production safety."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60  # 1 minute window
    
    entry = _rate_store.get(client_ip, (0, now))
    count, window_start = entry
    
    if now - window_start > window:
        # New window
        _rate_store[client_ip] = (1, now)
    elif count >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again in a minute."},
        )
    else:
        _rate_store[client_ip] = (count + 1, window_start)
    
    # Cleanup old entries periodically (every 100 requests)
    if len(_rate_store) > 500:
        cutoff = now - window * 2
        _rate_store.update({
            k: v for k, v in _rate_store.items() if v[1] > cutoff
        })
    
    return await call_next(request)


@app.on_event("startup")
async def startup_event():
    """Log essential startup information and run initial cleanup."""
    memory.cleanup_stale_sessions()
    memory.enforce_limit()
    logger.info("API Ready | Docs: /docs | Health: GET / | Honeypot: POST /honeypot")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors clearly."""
    logger.error(f"422 ERROR | {request.url.path} | {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Invalid request payload. See detail for exact fields.",
        },
    )


@app.get("/")
async def health_check():
    """Simple health check - lets the platform know we're alive."""
    return {
        "status": "online",
        "service": "Agentic Honey-Pot API",
        "version": "2.0.0",
        "languages": ["en", "hi"],
    }


@app.post("/honeypot", response_model=HoneypotResponse)
async def process_message(
    request: HoneypotRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process incoming scam messages and return analysis results."""
    try:
        import json
        
        session_id = request.sessionId
        current_message = request.message.text
        response_mode = getattr(request, "response_mode", None) or "rule_based"
        
        # Log full request body in one line
        request_dict = request.model_dump()
        logger.info(f"[{session_id[:8]}] REQUEST: {json.dumps(request_dict, ensure_ascii=False)}")
        
        # Process conversation history for context
        # First, update agent's context awareness from history
        agent.process_conversation_history(session_id, request.conversationHistory)
        
        for hist_msg in request.conversationHistory:
            if hist_msg.sender == "scammer":
                detector.calculate_risk_score(hist_msg.text, session_id)
                extractor.extract(hist_msg.text, session_id)
        
        memory.add_message(session_id, "scammer", current_message)
        
        # Analyze current message
        risk_score, is_scam = detector.calculate_risk_score(current_message, session_id)
        detection_details = detector.get_detection_details(session_id)
        
        if is_scam and not memory.is_scam_confirmed(session_id):
            memory.mark_scam_confirmed(session_id)
        
        # Generate internal agent response (not returned to client)
        scam_confirmed = memory.is_scam_confirmed(session_id)
        # Use actual conversation length from history, not just server memory count
        msg_count = len(request.conversationHistory) + 1
        
        # Always generate a rule-based reply first (authority)
        agent_reply = agent.get_reply(session_id, current_message, msg_count, scam_confirmed)
        reply_source = "rule_based"
        
        # If LLM mode requested and scam confirmed, try LLM rephrasing
        if response_mode == "llm" and scam_confirmed:
            strategy = agent.get_current_strategy(session_id)
            llm_reply, llm_source = await llm_service.rephrase_reply(
                strategy=strategy,
                rule_reply=agent_reply,
                scammer_message=current_message
            )
            agent_reply = llm_reply
            reply_source = llm_source
        
        memory.set_agent_response(session_id, agent_reply)
        memory.add_message(session_id, "agent", agent_reply)
        
        # Extract intelligence
        intelligence = extractor.extract(current_message, session_id)
        
        # Enrich suspiciousKeywords with detected categories for better analysis
        detected_categories = list(detection_details.triggered_categories)
        if detection_details.scam_type and detection_details.scam_type != "unknown":
            detected_categories.append(detection_details.scam_type)
        existing_keywords = intelligence.get("suspiciousKeywords", [])
        intelligence["suspiciousKeywords"] = list(set(existing_keywords + detected_categories))
        
        # Calculate metrics using conversation history length + 1
        total_messages = len(request.conversationHistory) + 1
        duration_seconds = memory.get_duration(session_id)
        
        # Generate notes with enhanced detection details (internal use only)
        if scam_confirmed:
            agent_notes = agent.generate_agent_notes(
                session_id, total_messages, intelligence, detection_details
            )
        else:
            agent_notes = agent.generate_monitoring_notes(session_id, total_messages)
        
        # Send callback if conditions met
        callback_sent = False
        callback_eligible = should_send_callback(scam_confirmed, total_messages, intelligence)
        
        if callback_eligible:
            if not memory.is_callback_sent(session_id):
                success = send_final_callback(session_id, total_messages, intelligence, agent_notes)
                if success:
                    memory.mark_callback_sent(session_id)
                    callback_sent = True
                    # Save callback record to DB
                    db_service.save_callback_record(
                        session_id=session_id,
                        status="sent",
                        payload_summary={
                            "totalMessages": total_messages,
                            "intelligenceCounts": {
                                "upiIds": len(intelligence.get("upiIds", [])),
                                "phoneNumbers": len(intelligence.get("phoneNumbers", [])),
                                "bankAccounts": len(intelligence.get("bankAccounts", [])),
                                "phishingLinks": len(intelligence.get("phishingLinks", [])),
                            }
                        }
                    )
        
        # Save session summary to DB (every message updates the summary)
        intel_counts = {
            "upiIds": len(intelligence.get("upiIds", [])),
            "phoneNumbers": len(intelligence.get("phoneNumbers", [])),
            "bankAccounts": len(intelligence.get("bankAccounts", [])),
            "phishingLinks": len(intelligence.get("phishingLinks", [])),
            "emails": len(intelligence.get("emails", [])),
            "suspiciousKeywords": len(intelligence.get("suspiciousKeywords", [])),
        }
        tactics_list = list(agent._get_context(session_id).get("detected_tactics", set()))
        db_service.save_session_summary(
            session_id=session_id,
            scam_type=detection_details.scam_type or "unknown",
            risk_level=detection_details.risk_level or "minimal",
            confidence=detection_details.confidence,
            message_count=total_messages,
            scam_detected=scam_confirmed,
            intelligence_counts=intel_counts,
            tactics=tactics_list,
            response_mode=reply_source,
            callback_sent=memory.is_callback_sent(session_id),
        )
        
        # Build response (status, reply, plus enriched metadata for UI)
        response = HoneypotResponse(
            status="success",
            reply=agent_reply,
            reply_source=reply_source,
            scam_detected=scam_confirmed,
            risk_score=risk_score,
            risk_level=detection_details.risk_level,
            confidence=detection_details.confidence,
            scam_type=detection_details.scam_type or "unknown",
            scam_stage=_get_scam_stage(msg_count, scam_confirmed, callback_sent),
            intelligence_counts=intel_counts,
            callback_sent=memory.is_callback_sent(session_id),
        )
        
        # Internal logging - detection result, intelligence, notes, callback (not exposed in response)
        internal_log = {
            "scamDetected": scam_confirmed,
            "replySource": reply_source,
            "engagementMetrics": {
                "engagementDurationSeconds": duration_seconds,
                "totalMessagesExchanged": total_messages
            },
            "extractedIntelligence": {
                "bankAccounts": intelligence.get("bankAccounts", []),
                "upiIds": intelligence.get("upiIds", []),
                "phishingLinks": intelligence.get("phishingLinks", []),
                "phoneNumbers": intelligence.get("phoneNumbers", []),
                "suspiciousKeywords": intelligence.get("suspiciousKeywords", [])
            },
            "agentNotes": agent_notes
        }
        logger.info(f"[{session_id[:8]}] INTERNAL: {json.dumps(internal_log, ensure_ascii=False)}")
        
        # Log simplified response
        response_dict = response.model_dump()
        logger.info(f"[{session_id[:8]}] RESPONSE: {json.dumps(response_dict, ensure_ascii=False)}")
        logger.info(f"[{session_id[:8]}] CALLBACK: {'sent' if callback_sent else 'not sent'}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


def _get_scam_stage(msg_count: int, scam_confirmed: bool, callback_sent: bool) -> str:
    """Determine the scam lifecycle stage."""
    if callback_sent:
        return "intelligence_reported"
    if scam_confirmed and msg_count >= 5:
        return "deep_engagement"
    if scam_confirmed:
        return "scam_confirmed"
    if msg_count >= 2:
        return "monitoring"
    return "initial_contact"


# ─── Read-Only Endpoints for UI ──────────────────────────────────────────────

@app.get("/sessions")
async def get_sessions(
    limit: int = Query(default=50, le=200),
    api_key: str = Depends(verify_api_key)
):
    """Get session summaries (no raw chats). For UI dashboard."""
    summaries = db_service.get_session_summaries(limit=limit)
    # Normalize DB records (camelCase) to snake_case for frontend
    normalized = []
    for s in summaries:
        normalized.append({
            "session_id": s.get("sessionId", ""),
            "scam_type": s.get("scamType", "unknown"),
            "risk_level": s.get("riskLevel", "minimal"),
            "confidence": s.get("confidence", 0.0),
            "message_count": s.get("messageCount", 0),
            "scam_confirmed": s.get("scamDetected", False),
            "intelligence_counts": s.get("intelligenceTypes", {}),
            "callback_sent": s.get("callbackSent", False),
            "response_mode": s.get("responseMode", "rule_based"),
            "tactics": s.get("tactics", []),
        })
    # Also include in-memory sessions not yet in DB
    for sid, session in memory.sessions.items():
        det = detector.get_detection_details(sid)
        normalized.append({
            "session_id": sid,
            "scam_confirmed": session.get("scamConfirmed", False),
            "message_count": session.get("messageCount", 0),
            "callback_sent": session.get("callbackSent", False),
            "risk_level": getattr(det, "risk_level", "minimal"),
            "scam_type": getattr(det, "scam_type", "unknown"),
            "confidence": getattr(det, "confidence", 0.0),
            "intelligence_counts": {},
            "active": True,
        })
    return {"sessions": normalized}


@app.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a single session's summary."""
    summary = db_service.get_session_summary(session_id)
    det = detector.get_detection_details(session_id)
    intel = extractor.get_intelligence_summary(session_id)
    return {
        "summary": summary,
        "detection": {
            "riskLevel": getattr(det, "risk_level", "minimal"),
            "confidence": getattr(det, "confidence", 0.0),
            "scamType": getattr(det, "scam_type", "unknown"),
            "riskScore": getattr(det, "total_score", 0),
        },
        "intelligenceCounts": intel,
    }


@app.get("/patterns")
async def get_patterns(api_key: str = Depends(verify_api_key)):
    """Get aggregated scam patterns and learning data."""
    return db_service.get_patterns()


@app.get("/callbacks")
async def get_callbacks(
    limit: int = Query(default=50, le=200),
    api_key: str = Depends(verify_api_key)
):
    """Get callback records for UI."""
    records = db_service.get_callback_records(limit=limit)
    # Normalize camelCase -> snake_case for frontend
    normalized = []
    for r in records:
        normalized.append({
            "session_id": r.get("sessionId", ""),
            "status": r.get("status", "unknown"),
            "payload_summary": r.get("payloadSummary", None),
            "timestamp": r.get("timestamp"),
        })
    return {"callbacks": normalized}


@app.get("/system/status")
async def get_system_status(api_key: str = Depends(verify_api_key)):
    """System status for settings panel."""
    return {
        "api": {"status": "online", "version": "2.0.0"},
        "llm": llm_service.get_status(),
        "database": db_service.get_status(),
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Agentic Honey-Pot API...")
    print("Make sure your .env file has API_KEY set")
    uvicorn.run(app, host="0.0.0.0", port=8000)
