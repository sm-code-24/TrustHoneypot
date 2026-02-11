"""
Advanced Scam Detection Engine with Multi-Signal Analysis.

This is a sophisticated detection system that goes beyond simple keyword matching.
It uses multiple detection strategies working together:

1. Weighted keyword scoring (base detection)
2. Pattern combination analysis (multiple signals = exponential risk)
3. India-specific scam templates (RBI, Aadhaar, PAN, govt impersonation)
4. Behavioral analysis (escalation patterns, urgency ramps)
5. Confidence scoring (not just yes/no, but how confident we are)
6. Scam type classification (identifies the specific scam variant)

This multi-layered approach catches sophisticated scammers who try to
avoid obvious keywords while still exhibiting scam behavior patterns.
"""
import re
from typing import Tuple, Dict, List, Set
from dataclasses import dataclass, field


@dataclass
class DetectionResult:
    """Detailed result of scam analysis."""
    total_score: int = 0
    is_scam: bool = False
    confidence: float = 0.0  # 0.0 to 1.0
    risk_level: str = "low"  # low, medium, high, critical
    scam_type: str = "unknown"
    detected_patterns: List[str] = field(default_factory=list)
    triggered_categories: Set[str] = field(default_factory=set)


class ScamDetector:
    """
    Advanced multi-signal scam detection engine.
    
    Uses a layered approach:
    - Layer 1: Keyword scoring (base signals)
    - Layer 2: Pattern combinations (compound signals)
    - Layer 3: India-specific patterns (regional context)
    - Layer 4: Behavioral analysis (message patterns)
    - Layer 5: Confidence calibration (certainty scoring)
    """
    
    # =========================================================================
    # LAYER 1: WEIGHTED KEYWORD SCORING
    # =========================================================================
    
    # Urgency tactics - scammers want you to act before you think
    URGENCY_KEYWORDS = {
        "urgent": 15, "immediately": 15, "right now": 12, "hurry": 12,
        "asap": 12, "quickly": 8, "fast action": 8,
        "expire": 15, "limited time": 15, "last chance": 18,
        "act now": 18, "don't wait": 12, "today only": 15,
        "within 24 hours": 18, "deadline": 12, "final notice": 20,
        "time sensitive": 15, "running out": 12, "expires today": 20,
        "hours left": 15, "minutes left": 18, "closing soon": 15,
        # Hindi urgency
        "jaldi karo": 12, "abhi karo": 10, "turant": 15,
        "jaldi": 10, "abhi": 8, "fauran": 12, "fatafat": 10,
        "der mat karo": 12, "waqt nahi hai": 15, "samay nahi hai": 15,
        "jald se jald": 15, "aaj hi": 12, "abhi ke abhi": 18,
        "rukiye mat": 10, "turat karo": 15, "jaldi kijiye": 12,
        "time khatam": 15, "akhri mauka": 18, "akhri chance": 18,
        "band ho jayega": 15, "expire ho jayega": 15,
    }
    
    # Account/verification scams - pretending to be your bank
    VERIFICATION_KEYWORDS = {
        "verify": 12, "confirm": 10, "update": 8,
        "account suspended": 22, "account blocked": 22, "blocked": 15,
        "deactivated": 18, "suspended": 18, "secure your": 12,
        "validate": 12, "authentication": 10, "kyc": 18,
        "reactivate": 15, "unlock": 12, "restore": 10,
        "verification required": 20, "verify immediately": 25,
        "re-kyc": 20, "kyc update": 18, "kyc expired": 22,
        "ekyc": 15, "video kyc": 18, "complete kyc": 18,
        "link aadhaar": 20, "link pan": 18, "update aadhaar": 18,
        # Hindi verification
        "khata band": 22, "account band": 22, "account band ho gaya": 25,
        "khata suspend": 22, "khata block": 22, "verify karo": 12,
        "verify karein": 12, "update karein": 10, "kyc karwao": 18,
        "kyc karo": 18, "khata band ho jayega": 25,
        "aadhaar link karo": 20, "pan link karo": 18,
    }
    
    # Money-related scams - lottery, refunds, prizes
    PAYMENT_KEYWORDS = {
        "refund": 18, "cashback": 15, "reward": 15,
        "prize": 20, "won": 18, "winner": 20, "lottery": 25,
        "transfer": 10, "payment": 8, "bank": 8,
        "upi": 12, "account number": 15, "ifsc": 12,
        "card": 10, "credit": 8, "debit": 8,
        "paytm": 10, "phonepe": 10, "googlepay": 10, "gpay": 10,
        "send money": 18, "pay now": 15, "processing fee": 20,
        "claim your": 18, "collect your": 15, "tax refund": 22,
        "income tax refund": 25, "gst refund": 22, "excess payment": 18,
        "double your money": 30, "guaranteed returns": 28, "investment scheme": 20,
        "crypto": 15, "bitcoin": 15, "trading profit": 22,
        # Hindi payment
        "paisa bhejo": 18, "paise bhejo": 18, "paise transfer karo": 20,
        "inaam": 20, "inam": 20, "lottery jeete": 25, "lottery nikli": 25,
        "cashback milega": 18, "refund aa raha": 20, "refund milega": 20,
        "paise wapas": 18, "paise katenge": 18, "processing fees": 20,
        "registration fees": 22, "jurmana": 18, "bhar do": 12,
        "raqam bhejo": 18, "paisa de do": 18, "bhariye": 12,
    }
    
    # Threats and intimidation - creating fear
    THREAT_KEYWORDS = {
        "legal action": 25, "police complaint": 20, "arrest warrant": 25,
        "penalty": 18, "heavy fine": 15, "court case": 20,
        "jail time": 25, "under investigation": 18, "case filed": 22,
        "arrest you": 25, "fraud case": 22, "cyber crime": 20,
        "legal notice": 22, "fir registered": 20, "fir filed": 20,
        "cbi case": 25, "enforcement directorate": 25, "e.d. case": 22,
        "money laundering case": 28, "hawala": 25, "terror funding": 30,
        "your name is involved": 22, "case registered against": 22,
        "digital arrest": 28, "video call arrest": 30,
        # Hindi threats
        "giraftar": 25, "giraftaar": 25, "arrest hoga": 25,
        "jail bhejenge": 25, "jail hogi": 25, "jail jayenge": 25,
        "case darj": 22, "case darj hoga": 25, "fir hogi": 22,
        "police bhejenge": 22, "police aa rahi hai": 25,
        "kanuni karwahi": 25, "kanooni karwai": 25,
        "muqadma": 22, "court mein": 20, "court ka notice": 22,
        "jurmana lagega": 18, "saza hogi": 22, "pakad lenge": 22,
        "warrant nikla hai": 25, "summon aaya hai": 22,
        "jaanch ho rahi hai": 18, "investigate ho raha": 18,
        "naam shamil hai": 22, "ghar pe aayenge": 22,
    }
    
    # =========================================================================
    # LAYER 2: INDIA-SPECIFIC SCAM PATTERNS (NEW!)
    # =========================================================================
    
    # Government impersonation - extremely common in India
    GOVT_IMPERSONATION = {
        "rbi": 25, "reserve bank": 25, "income tax": 20,
        "it department": 22, "customs": 20, "telecom department": 22,
        "trai": 22, "dot": 18, "department of telecom": 22,
        "ministry": 18, "government of india": 20, "goi": 15,
        "uidai": 22, "npci": 20, "sebi": 20, "irda": 18,
        "passport office": 18, "embassy": 18, "consulate": 18,
        "pmo": 25, "prime minister office": 25, "cm office": 22,
        "police commissioner": 22, "dgp": 22, "ips officer": 22,
        "central government": 20, "state government": 18,
        "pradhan mantri": 20, "pm scheme": 18, "govt scheme": 18,
        # Hindi govt impersonation
        "sarkar": 15, "sarkari": 15, "bharat sarkar": 20,
        "kendriya": 18, "mantralaya": 18,
        "police thana": 20, "thana": 15, "daroga": 18,
        "adhikari": 15, "inspector": 15, "sahab": 10,
        "sarkari yojana": 18, "vikas yojana": 15,
    }
    
    # Aadhaar/PAN specific scams - huge in India
    IDENTITY_SCAM = {
        "aadhaar": 15, "aadhar": 15, "pan card": 15,
        "aadhaar linked": 20, "pan linked": 18,
        "aadhaar will be blocked": 28, "pan will be suspended": 25,
        "aadhaar deactivated": 25, "pan deactivated": 25,
        "update aadhaar": 18, "aadhaar otp": 22,
        "aadhaar number used": 22, "pan number misused": 22,
        "multiple pan": 22, "duplicate aadhaar": 22,
        "aadhaar verification": 20, "pan verification": 18,
        "12 digit": 12, "10 digit pan": 12,
        # Hindi identity
        "aadhaar band": 25, "aadhaar block": 25,
        "pan band": 22, "pan block": 22,
        "aadhaar ka galat istemal": 28, "pan ka galat istemal": 25,
        "aadhaar link karo": 22, "pehchaan patra": 15,
    }
    
    # Telecom/SIM scams - very prevalent
    TELECOM_SCAM = {
        "sim block": 22, "sim deactivate": 22, "number will be blocked": 22,
        "illegal activities from your number": 28,
        "your number used for fraud": 25, "trai notice": 22,
        "telecom violation": 22, "sim verification": 18,
        "port your number": 15, "airtel": 10, "jio": 10, "vi": 10,
        "bsnl": 10, "mobile number linked": 15,
        # Hindi telecom
        "sim band hoga": 22, "sim band ho jayega": 25,
        "number band": 22, "number block": 22,
        "number se fraud hua": 28, "number ka galat istemal": 25,
    }
    
    # Courier/delivery scams
    COURIER_SCAM = {
        "parcel": 15, "courier": 15, "package": 12,
        "parcel seized": 25, "drugs found": 30, "illegal items": 28,
        "customs duty": 22, "package held": 20, "delivery failed": 15,
        "address verification": 18, "fedex": 12, "dhl": 12,
        "bluedart": 12, "delhivery": 10, "delivery boy": 10,
        # Hindi courier
        "parcel mein drugs": 30, "parcel pakda gaya": 25,
        "customs ne roka": 22, "saamaan roka gaya": 20,
        "parcel mein illegal": 28, "delivery ruk gayi": 15,
    }
    
    # Job/loan scams
    JOB_LOAN_SCAM = {
        "work from home": 18, "part time job": 18, "earn from home": 20,
        "typing job": 20, "data entry job": 18, "online job": 15,
        "instant loan": 22, "loan approved": 22, "pre-approved loan": 22,
        "processing charges": 20, "registration fee": 22,
        "advance payment": 22, "security deposit": 20,
        "earn daily": 20, "earn weekly": 18, "guaranteed income": 25,
        "no investment": 15, "investment required": 18,
        # Hindi job/loan
        "ghar baithe kaam": 20, "ghar baithe kamaiye": 22,
        "naukri": 12, "naukri milegi": 18, "rozgar": 12,
        "loan mil gaya": 22, "loan approved hai": 22,
        "advance dena hoga": 22, "registration fees do": 22,
        "roz kamao": 20, "daily kamai": 18, "paisa hi paisa": 25,
    }
    
    # =========================================================================
    # LAYER 3: PATTERN COMBINATIONS (COMPOUND SIGNALS)
    # =========================================================================
    
    # These patterns combine multiple signals - very high confidence when matched
    SCAM_TEMPLATES = [
        # RBI/Bank impersonation
        (r"(rbi|reserve bank|bank).{0,30}(kyc|verify|update|suspend|block)", 35, "bank_impersonation"),
        (r"(account|card).{0,20}(block|suspend|deactivat|terminat)", 30, "account_threat"),
        
        # Government impersonation + threat
        (r"(police|cbi|ed|cyber).{0,30}(case|arrest|warrant|investigation)", 40, "govt_threat"),
        (r"(aadhaar|aadhar|pan).{0,30}(block|suspend|deactivat|illegal|misuse)", 35, "identity_threat"),
        
        # Telecom scam pattern
        (r"(sim|number|mobile).{0,30}(block|deactivat|illegal|fraud)", 35, "telecom_scam"),
        (r"(trai|dot|telecom).{0,30}(notice|violation|complaint)", 32, "telecom_impersonation"),
        
        # Courier scam pattern
        (r"(parcel|courier|package).{0,30}(drugs|illegal|seiz|customs)", 40, "courier_scam"),
        
        # Money lure pattern
        (r"(won|winner|prize|lottery).{0,30}(claim|collect|receive|₹|\$)", 35, "lottery_scam"),
        (r"(refund|cashback).{0,30}(process|claim|receive|pending)", 30, "refund_scam"),
        
        # Job scam pattern
        (r"(job|work|earn).{0,30}(home|online|daily|weekly|guaranteed)", 28, "job_scam"),
        (r"(loan|credit).{0,30}(approved|sanction|instant|pre-approved)", 28, "loan_scam"),
        
        # OTP/credential fishing
        (r"(otp|password|pin|cvv).{0,20}(share|send|enter|provide)", 40, "credential_phishing"),
        (r"share.{0,20}(otp|password|pin|cvv)", 40, "credential_phishing"),
        
        # Urgency + action pattern
        (r"(urgent|immediate|asap).{0,30}(pay|transfer|send|click)", 32, "urgent_action"),
        
        # Digital arrest scam (trending in India)
        (r"(video|zoom|skype).{0,30}(arrest|custody|investigation)", 45, "digital_arrest"),
        (r"(digital|online).{0,20}arrest", 45, "digital_arrest"),
        
        # Investment scam
        (r"(invest|trading).{0,30}(guaranteed|double|triple|profit)", 35, "investment_scam"),
        (r"(crypto|bitcoin|forex).{0,30}(profit|return|guaranteed)", 35, "crypto_scam"),
        
        # Hindi compound patterns
        (r"(aadhaar|aadhar|pan).{0,30}(band|block|galat istemal|cancel)", 35, "identity_threat"),
        (r"(police|cbi|ed).{0,30}(bhejenge|aa rahi|pakad|giraftar)", 40, "govt_threat"),
        (r"(sim|number|mobile).{0,30}(band|block|galat istemal|fraud)", 35, "telecom_scam"),
        (r"(paisa|paise|raqam).{0,30}(bhejo|transfer|de do|jama)", 30, "payment_scam"),
        (r"(parcel|courier).{0,30}(drugs|pakda|roka|illegal)", 40, "courier_scam"),
        (r"(loan|naukri|kamai).{0,30}(milegi|approved|guaranteed|ghar baithe)", 28, "job_scam"),
        (r"(jail|giraftar|arrest).{0,20}(hoga|hogi|jayenge|karenge)", 40, "intimidation_scam"),
    ]
    
    # =========================================================================
    # LAYER 4: BEHAVIORAL PATTERNS
    # =========================================================================
    
    # These detect escalation patterns across messages
    ESCALATION_SIGNALS = [
        "last warning", "final chance", "we tried to contact",
        "this is your last", "if you don't respond", "action will be taken",
        "we are forced to", "no other option", "compelled to proceed",
        # Hindi escalation
        "aakhri warning", "aakhri chetavni", "akhri mauka",
        "karwahi hogi", "majboor hain", "jawab nahi diya toh",
        "koi aur rasta nahi", "aage badh jayenge",
    ]
    
    # Pressure tactics in sequence
    PRESSURE_SEQUENCE = [
        ("request", "remind", "warn", "final"),
        ("inform", "alert", "urgent", "critical"),
        ("pending", "overdue", "final", "legal")
    ]
    
    # =========================================================================
    # LAYER 5: SUSPICIOUS LINK PATTERNS
    # =========================================================================
    
    LINK_PATTERNS = [
        r"https?://[^\s]+",  # Any URL
        r"bit\.ly", r"tinyurl", r"goo\.gl", r"t\.co",  # URL shorteners
        r"click here", r"click this", r"tap here", r"click below",
        r"link:", r"visit:", r"open this",
        r"wa\.me", r"whatsapp\.com",  # WhatsApp links
        r"t\.me", r"telegram",  # Telegram links
        r"[a-z0-9]{8,}\.xyz", r"[a-z0-9]{8,}\.top",  # Suspicious TLDs
        r"[a-z0-9]{8,}\.online", r"[a-z0-9]{8,}\.site",
    ]
    
    # =========================================================================
    # THRESHOLDS AND CONFIGURATION
    # =========================================================================
    
    SCAM_THRESHOLD = 30  # Base threshold
    HIGH_CONFIDENCE_THRESHOLD = 60  # Very confident it's a scam
    CRITICAL_THRESHOLD = 100  # Definitely a scam
    
    # Category bonuses (hitting multiple categories = higher confidence)
    MULTI_CATEGORY_BONUS = {
        2: 10,   # 2 categories hit = +10
        3: 25,   # 3 categories hit = +25
        4: 45,   # 4 categories hit = +45
        5: 70,   # 5+ categories hit = +70
    }
    
    def __init__(self):
        self.session_scores: Dict[str, int] = {}
        self.session_details: Dict[str, DetectionResult] = {}
        self.session_categories: Dict[str, Set[str]] = {}
        self.session_message_count: Dict[str, int] = {}
    
    def _check_keywords(self, text: str, keyword_dict: dict, category: str, 
                        categories: set) -> int:
        """Check keywords using word boundary matching to avoid false positives."""
        score = 0
        text_lower = text.lower()
        for keyword, weight in keyword_dict.items():
            # Use word boundary regex to match whole words only
            # This prevents "know" from matching "now", "need" from matching "ed"
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                score += weight
                categories.add(category)
        return score
    
    def _check_patterns(self, text: str) -> Tuple[int, List[str], str]:
        """Check compound patterns and return score, matches, and scam type."""
        score = 0
        matches = []
        scam_type = "unknown"
        text_lower = text.lower()
        
        for pattern, weight, ptype in self.SCAM_TEMPLATES:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += weight
                matches.append(pattern)
                if scam_type == "unknown":
                    scam_type = ptype
        
        return score, matches, scam_type
    
    def _check_links(self, text: str) -> int:
        """Check for suspicious links."""
        for pattern in self.LINK_PATTERNS:
            if re.search(pattern, text.lower()):
                return 15
        return 0
    
    def _check_escalation(self, text: str) -> int:
        """Check for escalation signals."""
        score = 0
        text_lower = text.lower()
        for signal in self.ESCALATION_SIGNALS:
            if signal in text_lower:
                score += 12
        return score
    
    def _calculate_confidence(self, score: int, categories_hit: int, 
                              pattern_matches: int) -> float:
        """Calculate confidence level (0.0 to 1.0)."""
        if score < self.SCAM_THRESHOLD:
            return min(score / self.SCAM_THRESHOLD * 0.5, 0.5)
        
        # Base confidence from score
        if score >= self.CRITICAL_THRESHOLD:
            base = 0.95
        elif score >= self.HIGH_CONFIDENCE_THRESHOLD:
            base = 0.85
        else:
            base = 0.7
        
        # Boost for multiple categories
        category_boost = min(categories_hit * 0.03, 0.15)
        
        # Boost for pattern matches
        pattern_boost = min(pattern_matches * 0.05, 0.1)
        
        return min(base + category_boost + pattern_boost, 0.99)
    
    def _get_risk_level(self, score: int, confidence: float) -> str:
        """Determine risk level based on score and confidence."""
        if score >= self.CRITICAL_THRESHOLD or confidence >= 0.9:
            return "critical"
        elif score >= self.HIGH_CONFIDENCE_THRESHOLD or confidence >= 0.75:
            return "high"
        elif score >= self.SCAM_THRESHOLD:
            return "medium"
        elif score >= 15:
            return "low"
        else:
            return "minimal"
    
    def calculate_risk_score(self, text: str, session_id: str) -> Tuple[int, bool]:
        """
        Analyze a message and return its risk score.
        
        This is the main entry point. It runs all detection layers
        and returns a comprehensive analysis.
        
        Args:
            text: The message content to analyze
            session_id: Unique ID for this conversation
            
        Returns:
            (cumulative_score, is_scam) - total score so far and whether it's a scam
        """
        # Initialize session tracking
        if session_id not in self.session_categories:
            self.session_categories[session_id] = set()
            self.session_message_count[session_id] = 0
        
        self.session_message_count[session_id] += 1
        categories = self.session_categories[session_id]
        message_score = 0
        
        # LAYER 1: Keyword scoring
        all_keyword_dicts = [
            (self.URGENCY_KEYWORDS, "urgency"),
            (self.VERIFICATION_KEYWORDS, "verification"),
            (self.PAYMENT_KEYWORDS, "payment"),
            (self.THREAT_KEYWORDS, "threat"),
            (self.GOVT_IMPERSONATION, "govt_impersonation"),
            (self.IDENTITY_SCAM, "identity_scam"),
            (self.TELECOM_SCAM, "telecom_scam"),
            (self.COURIER_SCAM, "courier_scam"),
            (self.JOB_LOAN_SCAM, "job_loan_scam"),
        ]
        
        for keyword_dict, category in all_keyword_dicts:
            message_score += self._check_keywords(text, keyword_dict, category, categories)
        
        # LAYER 2: Pattern combination analysis
        pattern_score, pattern_matches, scam_type = self._check_patterns(text)
        message_score += pattern_score
        
        # LAYER 3: Suspicious links
        message_score += self._check_links(text)
        
        # LAYER 4: Escalation detection
        message_score += self._check_escalation(text)
        
        # LAYER 5: Multi-category bonus
        num_categories = len(categories)
        if num_categories >= 5:
            message_score += self.MULTI_CATEGORY_BONUS[5]
        elif num_categories >= 2:
            message_score += self.MULTI_CATEGORY_BONUS.get(num_categories, 0)
        
        # Update session score
        if session_id not in self.session_scores:
            self.session_scores[session_id] = 0
        
        self.session_scores[session_id] += message_score
        total_score = self.session_scores[session_id]
        
        # Calculate confidence and risk level
        confidence = self._calculate_confidence(
            total_score, num_categories, len(pattern_matches)
        )
        risk_level = self._get_risk_level(total_score, confidence)
        is_scam = total_score >= self.SCAM_THRESHOLD
        
        # Store detailed result
        self.session_details[session_id] = DetectionResult(
            total_score=total_score,
            is_scam=is_scam,
            confidence=confidence,
            risk_level=risk_level,
            scam_type=scam_type if scam_type != "unknown" else self._infer_scam_type(categories),
            detected_patterns=pattern_matches,
            triggered_categories=categories.copy()
        )
        
        return total_score, is_scam
    
    def _infer_scam_type(self, categories: Set[str]) -> str:
        """Infer scam type from triggered categories."""
        if "govt_impersonation" in categories:
            return "government_impersonation"
        elif "identity_scam" in categories:
            return "identity_theft"
        elif "telecom_scam" in categories:
            return "telecom_scam"
        elif "courier_scam" in categories:
            return "courier_scam"
        elif "job_loan_scam" in categories:
            return "job_loan_scam"
        elif "threat" in categories:
            return "intimidation_scam"
        elif "payment" in categories:
            return "payment_scam"
        elif "verification" in categories:
            return "phishing"
        else:
            return "generic_scam"
    
    def get_session_score(self, session_id: str) -> int:
        """Get the current risk score for a session."""
        return self.session_scores.get(session_id, 0)
    
    def get_detection_details(self, session_id: str) -> DetectionResult:
        """Get detailed detection result for a session."""
        return self.session_details.get(session_id, DetectionResult())
    
    def reset_session(self, session_id: str) -> None:
        """Clear score for a session (useful for testing)."""
        if session_id in self.session_scores:
            del self.session_scores[session_id]
        if session_id in self.session_details:
            del self.session_details[session_id]
        if session_id in self.session_categories:
            del self.session_categories[session_id]
        if session_id in self.session_message_count:
            del self.session_message_count[session_id]


# Single instance used across the app
detector = ScamDetector()
