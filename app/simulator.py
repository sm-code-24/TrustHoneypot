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
            "Yes sir, this is your correct number. The refund is registered against your mobile number. I just need 2 minutes to process it.",
            "Please open your UPI app now. I will send you a collect request. You just need to accept it to receive your refund.",
            "Sir I am sending Rs 2,499 to your account right now. Please enter your UPI PIN when you see the request.",
            "Sir the transaction failed because of some technical issue. Please try again and enter your UPI PIN carefully this time.",
            "Your bank server is blocking the refund. I will send a new link on your WhatsApp. Click it and enter your bank details to get refund.",
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
            "Sir if you do not complete KYC verification today itself, your mobile number will be permanently blocked. You will not be able to make calls.",
            "I am sending you an official verification link on SMS right now. Please click on it and fill in your Aadhaar number, PAN card, and bank details.",
            "Sir your verification OTP has been sent to your number. Please share the 6-digit OTP code with me right now so I can complete the KYC update.",
        ],
    },
    "digital_arrest": {
        "id": "digital_arrest",
        "name": "Digital Arrest Scam",
        "description": "Scammer impersonates CBI/Police and puts victim under 'digital arrest' via video call.",
        "language": "en",
        "scam_type": "digital_arrest",
        "difficulty": "hard",
        "messages": [
            "This is Inspector Sharma calling from Mumbai Cyber Crime Branch. Your Aadhaar number has been used in a money laundering case. A warrant has been issued.",
            "Sir this is a very serious matter. CBI and ED are involved. You need to stay on video call with me for verification. Do not disconnect or police will come.",
            "Sir you are now under digital arrest. You cannot leave your house or talk to anyone else. This is official CBI procedure. Stay on camera.",
            "Your bank accounts will be frozen unless you cooperate. Transfer your savings to this RBI safe custody account for verification: 12345678901.",
            "Sir if you disconnect this call, we will send police to your house immediately and arrest you in front of your family. This is your last warning.",
            "Transfer Rs 50,000 now to our verification account. Once cleared, all your money will be returned. UPI ID: cbi.safecustody@ybl",
        ],
    },
    "courier_drugs": {
        "id": "courier_drugs",
        "name": "Courier Parcel Scam",
        "description": "Scammer claims illegal drugs found in a parcel registered to victim's Aadhaar.",
        "language": "en",
        "scam_type": "courier_scam",
        "difficulty": "hard",
        "messages": [
            "This is calling from FedEx courier service. A parcel sent from your address to Iran has been seized at customs containing 5kg of illegal drugs.",
            "Sir this is a very serious matter. The parcel is registered to your Aadhaar number 2345-XXXX-6789. Narcotics Bureau has filed a case against you.",
            "I am connecting you to the cyber crime officer handling your case. Please stay on line. If you disconnect, police will be sent to your location.",
            "This is ACP Verma from Cyber Crime. Sir, your Aadhaar has been misused by an international drug syndicate. You need to verify your accounts immediately.",
            "To prove your innocence, you need to transfer all your bank balance to this RBI safe locker temporarily. It will be returned after investigation.",
            "Sir we need you to share your screen and show your bank accounts. This is for official documentation. Then transfer to account 98765432101 IFSC: SBIN0001234.",
        ],
    },
    "investment_scam": {
        "id": "investment_scam",
        "name": "Investment/Trading Scam",
        "description": "Scammer offers guaranteed returns on stock trading app.",
        "language": "en",
        "scam_type": "investment_scam",
        "difficulty": "medium",
        "messages": [
            "Hello sir! I am Priya from Golden Bull Trading Academy. We provide premium stock market tips with 100% guaranteed returns. Interested?",
            "Sir our members are making Rs 10,000-50,000 daily profit through our expert tips. Just last week Mr. Sharma from Delhi made Rs 2 lakhs!",
            "To join our premium group, you need to pay a one-time membership fee of Rs 4,999. After that, all tips are free forever.",
            "Sir I am sending you our exclusive trading app link. Download it and deposit Rs 5,000 minimum. Our experts will trade for you.",
            "Your account is ready! To speed up your first withdrawal, deposit Rs 10,000 more. This will unlock priority processing.",
            "Sir your profit of Rs 25,000 is ready but there is processing fee of Rs 4,500 for withdrawal. Please transfer to trader.bonus@axl",
        ],
    },
    "job_scam": {
        "id": "job_scam",
        "name": "Work From Home Job Scam",
        "description": "Scammer offers fake data entry job requiring registration fee.",
        "language": "hi",
        "scam_type": "job_scam",
        "difficulty": "easy",
        "messages": [
            "Namaste! Aapko ghar baithe data entry job chahiye? Daily 2-3 ghante kaam karke Rs 15,000-25,000 monthly kamao. WhatsApp group join karo.",
            "Ye bilkul genuine company hai ji. Amazon aur Flipkart ke saath tie-up hai. Typing speed achi ho toh Rs 30,000 bhi kama sakte ho.",
            "Registration ke liye sirf Rs 499 fee hai. Iske baad aapko laptop aur training material courier hoga. Sab company ki taraf se free.",
            "Ji aap Rs 499 ye UPI ID pe bhejiye: datafree.jobs@paytm. Payment confirm hote hi aapko login credentials mil jayenge.",
            "Bahut badiya! Registration successful. Ab upgrade package ke liye Rs 1,999 bhejiye. Isme direct client assignments milenge double salary ke saath.",
            "Sir aapka first payment Rs 5,000 ready hai! Bas withdrawal fee Rs 750 bhejiye account: 45678901234 IFSC: HDFC0001234",
        ],
    },
    "electricity_bill": {
        "id": "electricity_bill",
        "name": "Electricity Bill Scam",
        "description": "Scammer threatens to disconnect electricity unless immediate payment is made.",
        "language": "en",
        "scam_type": "utility_scam",
        "difficulty": "easy",
        "messages": [
            "URGENT: Your electricity connection will be disconnected today at 6 PM due to unpaid bill of Rs 8,450. This is final notice from BSES.",
            "Sir your bill has been overdue for 3 months. Our lineman is on the way to disconnect your meter. Do you want to pay now and stop disconnection?",
            "To make immediate payment and stop disconnection, please transfer Rs 8,450 to our official payment account right now.",
            "Sir, lineman has already reached your area. You have only 30 minutes. Transfer to this UPI: bses.payment@ybl immediately.",
            "Your payment is processing. Due to high load, you need to pay Rs 500 additional as convenience charge to same UPI ID.",
            "Sir one more OTP will come for final confirmation. Please share that code quickly so your electricity is not cut off.",
        ],
    },
    "aadhaar_misuse": {
        "id": "aadhaar_misuse",
        "name": "Aadhaar Misuse Threat",
        "description": "Scammer claims victim's Aadhaar is being misused in fraud and demands verification fee.",
        "language": "hi",
        "scam_type": "identity_scam",
        "difficulty": "medium",
        "messages": [
            "Hello sir, main UIDAI Aadhaar helpdesk se bol raha hoon. Aapke Aadhaar number ka galat istemal hua hai. 14 bank accounts aapke naam pe khule hain.",
            "Sir ye bahut serious matter hai. CBI aur Income Tax dono investigate kar rahe hain. Aapko apna Aadhaar verify karwana padega nahi toh jail ho sakti hai.",
            "Verification ke liye aapko Rs 2,999 security deposit dena hoga. Ye refundable hai. UIDAI ke official account mein jaayega.",
            "Sir jaldi kijiye, kal tak verification nahi hua toh aapka Aadhaar permanently block ho jayega. Koi bhi government work nahi hoga.",
            "UPI ID hai: aadhaar.secure@paytm. Rs 2,999 turant bhejiye aur apna Aadhaar number aur DOB bataiye verification ke liye.",
            "Sir agar aap abhi payment nahi karte toh hum police ko aapka address share karenge. Case already file ho chuka hai aapke khilaf.",
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
