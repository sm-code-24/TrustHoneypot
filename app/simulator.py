"""
Autonomous Chat Simulation - Demo Scam Scenarios

Provides predefined scam conversation templates for testing and demonstration.
Each scenario simulates a realistic multi-turn scam interaction.

Safe by design:
- All scammer messages use FAKE/placeholder data only
- No real phone numbers, bank accounts, or PII
- Designed purely for demonstration and testing purposes

INVARIANT: Uses the same detection/extraction/callback pipeline as real messages.
Does NOT modify detector scoring, extractor logic, or callback format.
"""
import uuid
import logging
from typing import Dict, List, Optional, Callable, Any

logger = logging.getLogger(__name__)


# ─── Demo Scenarios ───────────────────────────────────────────────────────────
# Each scenario has 5-6 escalating scammer messages that trigger different
# response stages from the honeypot agent.

SCENARIOS: Dict[str, dict] = {
    "bank_suspension": {
        "id": "bank_suspension",
        "name": "Bank Account Suspension",
        "description": "Scammer impersonates SBI and threatens account suspension unless KYC is updated immediately.",
        "language": "en",
        "scam_type": "bank_impersonation",
        "difficulty": "medium",
        "messages": [
            "Hello sir, this is calling from State Bank of India head office. Your savings account has been flagged for suspicious activity and will be suspended.",
            "Sir, your account will be permanently blocked within 24 hours if you don't verify your KYC immediately. This is very urgent.",
            "I need your account number and Aadhaar number for verification right now. This is a mandatory process under RBI guidelines.",
            "Sir please don't go to the branch, there is no time. I can help you verify online right now. Just share your details on this call.",
            "Sir to keep your account active you need to pay a small verification fee of Rs 999 to our official verification account. This is standard procedure.",
            "Our official UPI ID is sbi.verify@ybl. Please send Rs 999 immediately otherwise your pension deposit will be blocked from tomorrow.",
        ],
    },
    "upi_refund": {
        "id": "upi_refund",
        "name": "Fake UPI Refund",
        "description": "Scammer offers a fake refund through UPI reverse transaction to steal money.",
        "language": "en",
        "scam_type": "refund_scam",
        "difficulty": "easy",
        "messages": [
            "Hello! I am calling from Paytm customer support regarding your account. You have a pending refund of Rs 2,499 from a failed transaction last week.",
            "This refund has been approved by our finance team. I just need to process it for you right now. It will take only 2 minutes.",
            "Please open your UPI app now. I will send you a collect request. You just need to accept it to receive your refund.",
            "Sir I am sending Rs 2,499 to your account right now. Please enter your UPI PIN when prompted to receive the money.",
            "Sir the transaction failed because of some technical issue. Please try again and enter your UPI PIN carefully this time. The amount is Rs 2,499.",
            "Your bank server is blocking the refund. I will send a new link on your WhatsApp number 98XXXXX123. Click it and enter your bank details to get refund.",
        ],
    },
    "prize_lottery": {
        "id": "prize_lottery",
        "name": "KBC Prize Lottery",
        "description": "Scammer claims victim won KBC lucky draw and demands processing fee in Hindi.",
        "language": "hi",
        "scam_type": "lottery_scam",
        "difficulty": "medium",
        "messages": [
            "Namaste ji! Bahut badhai ho aapko! Aapka mobile number KBC ke lucky draw mein select hua hai. Aapko 10 lakh rupaye ka inam mila hai!",
            "Ji haan, ye Kaun Banega Crorepati ka official lucky draw hai. Amitabh Bachchan ji ne khud approve kiya hai. Bas ek chhoti si processing fee bhejni hai.",
            "Processing fee sirf Rs 5,999 hai ji. Ye tax aur documentation ke liye hai. Iske baad 10 lakh rupaye seedha aapke bank account mein transfer ho jayega.",
            "Jaldi kijiye sir, ye offer sirf aaj raat 12 baje tak valid hai. Agar aaj claim nahi kiya toh ye inam kisi aur lucky winner ko chala jayega.",
            "Paisa bhejne ke liye ye UPI ID use kijiye: kbc.prize2024@paytm. Turant Rs 5,999 bhejiye aur 10 lakh ka inam le jaiye ghar.",
            "Sir agar aap abhi processing fee nahi bhejte toh hamein majbooran police mein complaint file karni padegi kyunki government prize claim na karna offence hai.",
        ],
    },
    "fake_kyc": {
        "id": "fake_kyc",
        "name": "Fake KYC / SIM Block",
        "description": "Scammer impersonates Jio telecom and demands urgent KYC update or SIM will be deactivated.",
        "language": "en",
        "scam_type": "telecom_scam",
        "difficulty": "easy",
        "messages": [
            "URGENT: This is an automated alert from Jio. Your SIM card KYC verification is incomplete. Your number will be permanently deactivated within 24 hours.",
            "Sir this is Jio verification department calling. To continue using your mobile number, we need to verify your Aadhaar details immediately as per new TRAI guidelines.",
            "Please share your Aadhaar number and date of birth for verification. This is a mandatory government requirement. All telecom companies are doing this.",
            "Sir if you do not complete KYC verification today itself, your mobile number will be permanently blocked. You will not be able to make or receive any calls or messages.",
            "I am sending you an official verification link on SMS right now. Please click on it and fill in your Aadhaar number, PAN card, and bank details for complete KYC.",
            "Sir your verification OTP has been sent to your number. Please share the 6-digit OTP code with me right now so I can complete the KYC update on your behalf.",
        ],
    },
}


class ScamSimulator:
    """
    Runs autonomous scam simulations using predefined scenarios.
    
    Each simulation:
    1. Creates a unique session
    2. Sends each scammer message through the honeypot pipeline
    3. Collects agent responses, detection results, and extracted intel
    4. Returns the full conversation with analysis
    
    Uses the SAME pipeline as real messages (detector → agent → extractor → callback).
    Does NOT bypass or modify any detection/extraction logic.
    """
    
    def get_scenarios(self) -> List[dict]:
        """Return list of available demo scenarios (metadata only)."""
        return [
            {
                "id": s["id"],
                "name": s["name"],
                "description": s["description"],
                "language": s["language"],
                "scam_type": s["scam_type"],
                "difficulty": s["difficulty"],
                "message_count": len(s["messages"]),
            }
            for s in SCENARIOS.values()
        ]
    
    def get_scenario(self, scenario_id: str) -> Optional[dict]:
        """Get a single scenario by ID."""
        return SCENARIOS.get(scenario_id)
    
    async def run_simulation(
        self,
        scenario_id: str,
        response_mode: str = "rule_based",
        honeypot_handler: Optional[Callable[..., Any]] = None,
    ) -> dict:
        """
        Run a full simulation for a given scenario.
        
        Args:
            scenario_id: ID of the scenario to run
            response_mode: "rule_based" or "llm"
            honeypot_handler: Async function that processes a single message
                              through the honeypot pipeline. Signature:
                              (session_id, message_text, history, response_mode) -> dict
        
        Returns:
            Full simulation result with conversation, analysis, and stage progression
        """
        scenario = SCENARIOS.get(scenario_id)
        if not scenario:
            return {"error": f"Unknown scenario: {scenario_id}"}
        
        if not honeypot_handler:
            return {"error": "No honeypot handler provided"}
        
        session_id = f"sim-{uuid.uuid4().hex[:12]}"
        conversation: List[dict] = []
        stage_progression: List[dict] = []
        final_analysis = None
        
        logger.info(f"[SIMULATION] Starting scenario '{scenario_id}' | session={session_id}")
        
        for i, scammer_msg in enumerate(scenario["messages"]):
            # Build conversation history (previous messages)
            history = [
                {"sender": m["sender"], "text": m["text"]}
                for m in conversation
            ]
            
            # Process through honeypot pipeline
            try:
                result = await honeypot_handler(
                    session_id, scammer_msg, history, response_mode
                )
            except Exception as e:
                logger.error(f"[SIMULATION] Error at message {i+1}: {e}")
                conversation.append({
                    "sender": "scammer",
                    "text": scammer_msg,
                    "step": i + 1,
                })
                conversation.append({
                    "sender": "system",
                    "text": f"Error: {str(e)}",
                    "step": i + 1,
                })
                continue
            
            # Record scammer message
            conversation.append({
                "sender": "scammer",
                "text": scammer_msg,
                "step": i + 1,
            })
            
            # Record agent response
            conversation.append({
                "sender": "agent",
                "text": result.get("reply", ""),
                "reply_source": result.get("reply_source", "rule_based"),
                "step": i + 1,
            })
            
            # Track stage progression
            stage_info = result.get("stage_info")
            if stage_info:
                stage_progression.append({
                    "step": i + 1,
                    "stage": stage_info.get("stage"),
                    "label": stage_info.get("label"),
                    "progress": stage_info.get("progress"),
                    "agent_confidence": stage_info.get("agent_confidence", 0),
                })
            
            final_analysis = result
            
            # If callback was sent, simulation is complete
            if result.get("callback_sent"):
                logger.info(f"[SIMULATION] Callback triggered at step {i+1}")
                break
        
        logger.info(
            f"[SIMULATION] Complete | scenario={scenario_id} "
            f"messages={len(conversation)} "
            f"scam_detected={final_analysis.get('scam_detected') if final_analysis else False}"
        )
        
        return {
            "simulation_id": session_id,
            "scenario": {
                "id": scenario["id"],
                "name": scenario["name"],
                "description": scenario["description"],
                "language": scenario["language"],
                "scam_type": scenario["scam_type"],
            },
            "conversation": conversation,
            "stage_progression": stage_progression,
            "final_analysis": {
                "scam_detected": final_analysis.get("scam_detected", False) if final_analysis else False,
                "risk_score": final_analysis.get("risk_score", 0) if final_analysis else 0,
                "risk_level": final_analysis.get("risk_level", "minimal") if final_analysis else "minimal",
                "confidence": final_analysis.get("confidence", 0) if final_analysis else 0,
                "scam_type": final_analysis.get("scam_type", "unknown") if final_analysis else "unknown",
                "callback_sent": final_analysis.get("callback_sent", False) if final_analysis else False,
                "intelligence_counts": final_analysis.get("intelligence_counts", {}) if final_analysis else {},
            },
            "total_messages": len(conversation),
            "response_mode": response_mode,
        }


# Singleton
simulator = ScamSimulator()
