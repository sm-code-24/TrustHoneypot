"""
Callback module for reporting scam intelligence to government portals.

When the honeypot gathers enough evidence on a confirmed scam, this module
automatically submits the extracted intelligence to the configured
government reporting endpoint.
"""
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Government portal endpoint where we submit scam intelligence
CALLBACK_URL = os.getenv("CALLBACK_URL", "")

# File to store callback history for debugging/audit
CALLBACK_LOG_FILE = "callback_history.json"


def _log_callback(session_id: str, payload: dict, response_status: int, response_text: str, success: bool):
    """Persist callback details to JSON file for audit trail AND log to stdout."""
    callback_record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sessionId": session_id,
        "success": success,
        "responseStatus": response_status,
        "responseText": response_text[:500] if response_text else "",
        "payload": payload
    }
    
    # IMPORTANT: Log to stdout for Railway logs (always visible)
    logger.info(f"📞 CALLBACK RECORD: {json.dumps(callback_record, indent=None)}")
    
    try:
        # Also save to local file (works locally, not on Railway)
        if os.path.exists(CALLBACK_LOG_FILE):
            with open(CALLBACK_LOG_FILE, "r") as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(callback_record)
        
        with open(CALLBACK_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)
            
    except Exception as e:
        logger.warning(f"Failed to log callback to file: {e}")


def send_final_callback(
    session_id: str,
    total_messages: int,
    intelligence: dict,
    agent_notes: str
) -> tuple:
    """
    Send final scam intelligence to the configured government portal.
    
    This gets called once per session when we have:
    - Confirmed it's a scam
    - Engaged enough to gather intel  
    - Extracted at least one piece of useful info
    
    Returns (status, payload) where status is one of:
        "sent"        — external portal accepted the callback
        "failed"      — external portal rejected or network error
        "no_endpoint" — no CALLBACK_URL configured (still recorded internally)
    """
    # Build payload matching the expected government portal format
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": intelligence.get("bankAccounts", []),
            "upiIds": intelligence.get("upiIds", []),
            "phishingLinks": intelligence.get("phishingLinks", []),
            "phoneNumbers": intelligence.get("phoneNumbers", []),
            "suspiciousKeywords": intelligence.get("suspiciousKeywords", []),
        },
        "agentNotes": agent_notes
    }
    
    # If no endpoint is configured, record the payload but skip the HTTP call
    if not CALLBACK_URL:
        logger.info(f"📋 CALLBACK RECORDED (no endpoint configured) for session {session_id}")
        logger.info(f"📋 CALLBACK PAYLOAD: {json.dumps(payload, ensure_ascii=False)[:800]}")
        _log_callback(session_id, payload, 0, "No CALLBACK_URL configured", False)
        return "no_endpoint", payload
    
    try:
        logger.info(f"🚀 SENDING CALLBACK for session {session_id} to {CALLBACK_URL}")
        logger.info(f"🚀 CALLBACK PAYLOAD: {json.dumps(payload, ensure_ascii=False)[:800]}")
        
        response = requests.post(
            CALLBACK_URL,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        # 200, 201, 204 all mean success
        if response.status_code in [200, 201, 204]:
            logger.info(f"Callback accepted for session {session_id}")
            _log_callback(session_id, payload, response.status_code, response.text, True)
            return "sent", payload
        else:
            logger.error(f"Callback rejected: {response.status_code} - {response.text}")
            _log_callback(session_id, payload, response.status_code, response.text, False)
            return "failed", payload
            
    except requests.exceptions.Timeout:
        logger.error("Callback timed out after 10 seconds")
        _log_callback(session_id, payload, 0, "Timeout after 10 seconds", False)
        return "failed", payload
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error sending callback: {str(e)}")
        _log_callback(session_id, payload, 0, f"Network error: {str(e)}", False)
        return "failed", payload
    except Exception as e:
        logger.error(f"Unexpected error in callback: {str(e)}")
        _log_callback(session_id, payload, 0, f"Unexpected error: {str(e)}", False)
        return "failed", payload


def should_send_callback(scam_detected: bool, total_messages: int, intelligence: dict) -> bool:
    """
    Check if conditions are met to send the callback.
    
    Callback should only be sent when:
    1. Scam intent is confirmed (scamDetected = true)
    2. AI Agent has completed sufficient engagement (3+ messages)
    3. At least one actionable identifier extracted (UPI, bank, phone, link, or email)
       — keywords alone are NOT enough for law enforcement
    
    This is the FINAL step of the conversation lifecycle.
    """
    bank_ct = len(intelligence.get("bankAccounts", []))
    upi_ct = len(intelligence.get("upiIds", []))
    link_ct = len(intelligence.get("phishingLinks", []))
    phone_ct = len(intelligence.get("phoneNumbers", []))
    email_ct = len(intelligence.get("emails", []))
    keyword_ct = len(intelligence.get("suspiciousKeywords", []))
    has_intel = any([bank_ct > 0, upi_ct > 0, link_ct > 0, phone_ct > 0, email_ct > 0])
    
    eligible = scam_detected and total_messages >= 3 and has_intel
    
    # Always log eligibility for debugging deployed issues
    logger.info(
        f"📋 CALLBACK ELIGIBILITY: eligible={eligible} | "
        f"scam_detected={scam_detected}, total_messages={total_messages}(need>=3), "
        f"has_intel={has_intel} [bank={bank_ct}, upi={upi_ct}, links={link_ct}, phone={phone_ct}, email={email_ct}], "
        f"keywords={keyword_ct}"
    )
    if not eligible:
        reasons = []
        if not scam_detected:
            reasons.append("scam NOT confirmed")
        if total_messages < 3:
            reasons.append(f"only {total_messages} messages (need 3+)")
        if not has_intel:
            reasons.append("NO actionable identifiers extracted (need at least one: UPI/bank/phone/link/email)")
        logger.warning(f"⚠️ CALLBACK NOT ELIGIBLE: {', '.join(reasons)}")
    
    return eligible
