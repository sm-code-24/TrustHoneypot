"""
Agentic Honey-Pot API v2.0.0
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
    HoneypotResponse,
    SimulationRequest,
    SimulationResponse,
)
from auth import verify_api_key
from detector import detector
from extractor import extractor
from agent import agent
from memory import memory
from callback import send_final_callback, should_send_callback
from llm import llm_service
from db import db_service
from simulator import simulator

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
_default_origins = "https://trusthoneypot.tech,https://www.trusthoneypot.tech,http://localhost:5173,http://localhost:3000"
_allowed_origins = os.getenv("CORS_ORIGINS", _default_origins).split(",")
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


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await llm_service.close()
    logger.info("API shutdown complete")


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
        logger.info(f"[SESSION] [{session_id[:8]}] REQUEST: {json.dumps(request_dict, ensure_ascii=False)}")
        
        # Process conversation history for context
        # First, update agent's context awareness from history
        agent.process_conversation_history(session_id, request.conversationHistory)
        
        # Only process NEW history messages through detector/extractor
        # (avoid re-scoring the same messages on every request, which inflates risk scores)
        _history_key = f"_detector_hist_{session_id}"
        _already_processed = memory.sessions.get(session_id, {}).get("_detector_history_count", 0)
        _new_history = request.conversationHistory[_already_processed:]
        for hist_msg in _new_history:
            if hist_msg.sender == "scammer":
                detector.calculate_risk_score(hist_msg.text, session_id)
                extractor.extract(hist_msg.text, session_id)
        memory.create_session(session_id)
        memory.sessions[session_id]["_detector_history_count"] = len(request.conversationHistory)
        
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
        
        # If LLM mode requested, try LLM rephrasing (works for ALL replies, not just confirmed scams)
        if response_mode == "llm":
            logger.info(f"[{session_id[:8]}] [LLM] Mode requested. enabled={llm_service.enabled}, api_key_set={bool(llm_service.api_key)}, model={llm_service.model_name}")
            if not llm_service.enabled:
                llm_status = llm_service.get_status()
                logger.warning(f"[{session_id[:8]}] [LLM] NOT ENABLED — status: {json.dumps(llm_status)}")
                reply_source = "rule_based_fallback"
            else:
                strategy = agent.get_current_strategy(session_id)
                try:
                    llm_reply, llm_source = await llm_service.rephrase_reply(
                        strategy=strategy,
                        rule_reply=agent_reply,
                        scammer_message=current_message
                    )
                    agent_reply = llm_reply
                    reply_source = llm_source
                except Exception as llm_err:
                    logger.warning(f"[{session_id[:8]}] [LLM] Rephrase failed: {llm_err}, using rule-based")
                    print(f"[LLM] Rephrase failed: {llm_err}")
                    reply_source = "rule_based_fallback"
        
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
        logger.info(f"[CALLBACK] [{session_id[:8]}] Checking eligibility: scam={scam_confirmed}, msgs={total_messages}, intel={json.dumps({k: len(v) if isinstance(v, list) else v for k, v in intelligence.items()}, ensure_ascii=False)}")
        callback_eligible = should_send_callback(scam_confirmed, total_messages, intelligence)
        
        if callback_eligible:
            already_sent = memory.is_callback_sent(session_id)
            logger.info(f"[CALLBACK] [{session_id[:8]}] ELIGIBLE! already_sent={already_sent}")
            if not already_sent:
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
        stage_info = agent.get_engagement_stage(session_id, msg_count, scam_confirmed, callback_sent)
        
        response = HoneypotResponse(
            status="success",
            reply=agent_reply,
            reply_source=reply_source,
            scam_detected=scam_confirmed,
            risk_score=risk_score,
            risk_level=detection_details.risk_level,
            confidence=detection_details.confidence,
            scam_type=detection_details.scam_type or "unknown",
            scam_stage=stage_info["stage"],
            stage_info=stage_info,
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
        logger.info(f"[AGENT] [{session_id[:8]}] INTERNAL: {json.dumps(internal_log, ensure_ascii=False)}")
        
        # Log simplified response
        response_dict = response.model_dump()
        logger.info(f"[SESSION] [{session_id[:8]}] RESPONSE: {json.dumps(response_dict, ensure_ascii=False)}")
        logger.info(f"[CALLBACK] [{session_id[:8]}] FINAL_STATUS={'SENT ✅' if callback_sent else 'NOT_SENT ❌'} eligible={callback_eligible} already_sent_prev={memory.is_callback_sent(session_id) and not callback_sent}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


def _get_scam_stage(msg_count: int, scam_confirmed: bool, callback_sent: bool) -> str:
    """Determine the scam lifecycle stage (legacy helper, prefer agent.get_engagement_stage)."""
    if callback_sent:
        return "intelligence_reported"
    if scam_confirmed and msg_count >= 5:
        return "deep_engagement"
    if scam_confirmed:
        return "scam_confirmed"
    if msg_count >= 2:
        return "monitoring"
    return "initial_contact"


# ─── Simulation Endpoints ─────────────────────────────────────────────────────

@app.get("/scenarios")
async def get_scenarios(api_key: str = Depends(verify_api_key)):
    """List available demo scam scenarios for auto-simulation."""
    return {"scenarios": simulator.get_scenarios()}


@app.post("/simulate", response_model=SimulationResponse)
async def run_simulation(
    request: SimulationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Run an autonomous scam simulation with a predefined scenario.
    
    The simulation processes each scammer message through the full honeypot
    pipeline (detection → agent response → extraction → callback check).
    Returns the complete conversation with stage progression and analysis.
    """
    import json as _json
    
    scenario = simulator.get_scenario(request.scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{request.scenario_id}' not found. Use GET /scenarios for available options."
        )
    
    async def honeypot_handler(session_id, message_text, history, response_mode):
        """Internal handler that mirrors /honeypot logic for simulation."""
        from models import Message
        
        # Build message history objects
        history_msgs = [Message(sender=h["sender"], text=h["text"]) for h in history]
        
        # Process conversation history (only new messages)
        agent.process_conversation_history(session_id, history_msgs)
        
        _already = memory.sessions.get(session_id, {}).get("_detector_history_count", 0)
        for hist_msg in history_msgs[_already:]:
            if hist_msg.sender == "scammer":
                detector.calculate_risk_score(hist_msg.text, session_id)
                extractor.extract(hist_msg.text, session_id)
        memory.create_session(session_id)
        memory.sessions[session_id]["_detector_history_count"] = len(history_msgs)
        
        memory.add_message(session_id, "scammer", message_text)
        
        # Analyze current message
        risk_score, is_scam = detector.calculate_risk_score(message_text, session_id)
        detection_details = detector.get_detection_details(session_id)
        
        if is_scam and not memory.is_scam_confirmed(session_id):
            memory.mark_scam_confirmed(session_id)
        
        scam_confirmed = memory.is_scam_confirmed(session_id)
        msg_count = len(history) + 1
        
        # Generate agent reply
        agent_reply = agent.get_reply(session_id, message_text, msg_count, scam_confirmed)
        reply_source = "rule_based"
        
        # LLM rephrasing if requested
        if response_mode == "llm":
            strategy = agent.get_current_strategy(session_id)
            try:
                llm_reply, llm_source = await llm_service.rephrase_reply(
                    strategy=strategy,
                    rule_reply=agent_reply,
                    scammer_message=message_text
                )
                agent_reply = llm_reply
                reply_source = llm_source
            except Exception:
                reply_source = "rule_based_fallback"
        
        memory.set_agent_response(session_id, agent_reply)
        memory.add_message(session_id, "agent", agent_reply)
        
        # Extract intelligence
        intelligence = extractor.extract(message_text, session_id)
        intel_counts = {
            "upiIds": len(intelligence.get("upiIds", [])),
            "phoneNumbers": len(intelligence.get("phoneNumbers", [])),
            "bankAccounts": len(intelligence.get("bankAccounts", [])),
            "phishingLinks": len(intelligence.get("phishingLinks", [])),
            "emails": len(intelligence.get("emails", [])),
            "suspiciousKeywords": len(intelligence.get("suspiciousKeywords", [])),
        }
        
        # Check callback
        total_messages = len(history) + 1
        callback_sent = False
        callback_eligible = should_send_callback(scam_confirmed, total_messages, intelligence)
        if callback_eligible and not memory.is_callback_sent(session_id):
            agent_notes = agent.generate_agent_notes(session_id, total_messages, intelligence, detection_details)
            success = send_final_callback(session_id, total_messages, intelligence, agent_notes)
            if success:
                memory.mark_callback_sent(session_id)
                callback_sent = True
                # Save callback record to DB (was missing in simulation handler!)
                db_service.save_callback_record(
                    session_id=session_id,
                    status="sent",
                    payload_summary={
                        "totalMessages": total_messages,
                        "intelligenceCounts": intel_counts,
                        "source": "simulation",
                    }
                )
                logger.info(f"[SIM] [{session_id[:8]}] Callback record saved to DB")
        
        # Save session summary to DB (was missing in simulation handler!)
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
        
        stage_info = agent.get_engagement_stage(session_id, msg_count, scam_confirmed, callback_sent or memory.is_callback_sent(session_id))
        
        return {
            "reply": agent_reply,
            "reply_source": reply_source,
            "scam_detected": scam_confirmed,
            "risk_score": risk_score,
            "risk_level": detection_details.risk_level,
            "confidence": detection_details.confidence,
            "scam_type": detection_details.scam_type or "unknown",
            "scam_stage": stage_info["stage"],
            "stage_info": stage_info,
            "intelligence_counts": intel_counts,
            "callback_sent": callback_sent or memory.is_callback_sent(session_id),
        }
    
    logger.info(f"[SIMULATION] Request: scenario={request.scenario_id} mode={request.response_mode}")
    
    result = await simulator.run_simulation(
        scenario_id=request.scenario_id,
        response_mode=request.response_mode,
        honeypot_handler=honeypot_handler,
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


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
        # Convert timestamp to ISO format string with timezone
        ts = r.get("timestamp")
        if ts:
            if hasattr(ts, 'isoformat'):
                ts = ts.isoformat()
            # Ensure it ends with Z for UTC
            if isinstance(ts, str) and not ts.endswith('Z') and '+' not in ts:
                ts = ts + 'Z'
        normalized.append({
            "session_id": r.get("sessionId", ""),
            "status": r.get("status", "unknown"),
            "payload_summary": r.get("payloadSummary", None),
            "timestamp": ts,
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
