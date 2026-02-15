"""
Lightweight NLP Intent Classifier — TrustHoneypot v2.2

Classifies each incoming message into one of 12 intent categories using
regex + keyword + weighted scoring. Each intent carries a risk_score_increment
that feeds into the cumulative session risk score.

This classifier runs BEFORE the scam detector and provides:
  - Intent label (GREETING, SELF_INTRO, SMALL_TALK, etc.)
  - Risk score increment (0 to +50)
  - Matched keywords for transparency

Architecture invariant: this is fully rule-based. No LLM involvement.
"""
import re
from typing import Dict, List, Tuple

# ── Intent Definitions ─────────────────────────────────────────────────────
# Each intent: (keywords/patterns, risk_score_increment)

INTENT_CATALOG: Dict[str, Dict] = {
    "GREETING": {
        "risk": 0,
        "keywords": [
            "hi", "hello", "hey", "hii", "hiii", "helo",
            "good morning", "good afternoon", "good evening", "good night",
            "gm", "gn", "morning", "evening",
            "namaste", "namaskar", "namaskaaram",
            "howdy", "greetings", "sup", "yo",
            "haan ji", "ji", "haanji",
        ],
        "max_words": 4,
    },
    "SELF_INTRO": {
        "risk": 0,
        "keywords": [
            "my name is", "i am calling from", "this is", "speaking from",
            "i'm from", "calling from", "mera naam", "main bol raha",
            "department se", "ministry se", "bank se bol raha",
            "officer", "inspector", "sir ji main",
        ],
        "max_words": None,
    },
    "SMALL_TALK": {
        "risk": 0,
        "keywords": [
            "how are you", "kaise ho", "kya haal", "everything ok",
            "how is your health", "tabiyat kaisi", "sab theek",
            "what are you doing", "kya kar rahe", "good good",
            "nice to talk", "achha hai", "theek hai ji",
        ],
        "max_words": None,
    },
    "IDENTITY_PROBE": {
        "risk": 5,
        "keywords": [
            "what is your name", "naam kya hai", "aapka naam",
            "where do you live", "kahan rehte", "address kya hai",
            "your aadhaar", "your pan", "your account",
            "date of birth", "dob", "father name", "mother name",
            "pita ka naam", "mata ka naam",
        ],
        "max_words": None,
    },
    "TOPIC_PROBE": {
        "risk": 5,
        "keywords": [
            "do you know", "have you heard", "are you aware",
            "did you receive", "aapko pata hai", "suna hai aapne",
            "notice mila", "letter aaya", "email aaya",
            "sms aaya kya", "notification aaya",
        ],
        "max_words": None,
    },
    "URGENCY": {
        "risk": 30,
        "keywords": [
            "immediately", "right now", "urgent", "hurry", "asap",
            "within 24 hours", "within 1 hour", "time is running",
            "last chance", "final notice", "deadline", "expires today",
            "abhi karo", "turant", "jaldi karo", "fauran",
            "der mat karo", "waqt nahi hai", "akhri mauka",
            "abhi ke abhi", "aaj hi karna hoga", "band ho jayega",
        ],
        "max_words": None,
    },
    "PAYMENT_REQUEST": {
        "risk": 40,
        "keywords": [
            "send money", "transfer money", "pay now", "pay immediately",
            "processing fee", "registration fee", "fine", "penalty amount",
            "send to this account", "send to this upi",
            "paisa bhejo", "paise transfer karo", "amount bhejo",
            "raqam bhejo", "fees bhariye", "jurmana bharo",
            "neft karo", "imps karo", "upi se bhejo",
        ],
        "max_words": None,
    },
    "BANK_REQUEST": {
        "risk": 40,
        "keywords": [
            "account number", "bank account", "ifsc code",
            "debit card number", "credit card number", "card number",
            "cvv", "expiry date", "pin number", "atm pin",
            "khata number batao", "card ka number",
            "account details do", "bank details chahiye",
        ],
        "max_words": None,
    },
    "OTP_REQUEST": {
        "risk": 50,
        "keywords": [
            "share otp", "send otp", "tell otp", "otp batao",
            "otp bhejo", "otp share karo", "verification code",
            "6 digit code", "one time password",
            "code batao", "code share karo", "otp kya aaya",
            "otp forward karo",
        ],
        "max_words": None,
    },
    "LEGAL_THREAT": {
        "risk": 35,
        "keywords": [
            "arrest warrant", "fir filed", "fir registered",
            "legal action", "court case", "police complaint",
            "jail", "prison", "custody", "investigation",
            "giraftar", "jail bhejenge", "case darj",
            "warrant nikla", "police bhejenge", "kanooni karwai",
            "arrest hoga", "pakad lenge",
        ],
        "max_words": None,
    },
    "ESCALATION": {
        "risk": 25,
        "keywords": [
            "last warning", "final chance", "if you don't respond",
            "action will be taken", "no other option",
            "we are forced", "compelled to proceed",
            "aakhri warning", "aakhri chetavni", "majboor hain",
            "jawab nahi diya toh", "karwahi hogi",
            "consequences", "you will regret", "don't blame us",
        ],
        "max_words": None,
    },
    "GENERIC_TEXT": {
        "risk": 0,
        "keywords": [],
        "max_words": None,
    },
}


def classify_intent(text: str) -> Dict:
    """
    Classify a message into one of 12 intent categories.

    Returns:
        {
            "intent": str,           # e.g. "GREETING", "URGENCY"
            "risk_increment": int,   # 0 to 50
            "matched_keywords": list # which keywords matched
        }
    """
    cleaned = text.strip().lower()
    words = cleaned.split()
    word_count = len(words)

    best_intent = "GENERIC_TEXT"
    best_risk = 0
    best_matches: List[str] = []
    best_priority = -1

    # Priority order: higher-risk intents take precedence when multiple match
    priority_order = [
        "OTP_REQUEST", "PAYMENT_REQUEST", "BANK_REQUEST", "LEGAL_THREAT",
        "URGENCY", "ESCALATION", "IDENTITY_PROBE", "TOPIC_PROBE",
        "SMALL_TALK", "SELF_INTRO", "GREETING", "GENERIC_TEXT",
    ]

    for priority, intent_name in enumerate(priority_order):
        spec = INTENT_CATALOG[intent_name]
        keywords = spec["keywords"]
        max_words = spec.get("max_words")

        if not keywords:
            continue

        # For GREETING: enforce max_words constraint
        if max_words is not None and word_count > max_words:
            continue

        matched = []
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, cleaned):
                matched.append(kw)

        if matched:
            intent_risk = spec["risk"]
            # Higher risk intents always win; among equal risk, first match wins
            if intent_risk > best_risk or (intent_risk == best_risk and priority < best_priority):
                best_intent = intent_name
                best_risk = intent_risk
                best_matches = matched
                best_priority = priority

    return {
        "intent": best_intent,
        "risk_increment": best_risk,
        "matched_keywords": best_matches,
    }


def get_intent_risk(text: str) -> Tuple[str, int]:
    """Convenience: returns (intent_name, risk_increment)."""
    result = classify_intent(text)
    return result["intent"], result["risk_increment"]
