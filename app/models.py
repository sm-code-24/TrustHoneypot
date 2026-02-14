"""
Data models for the Honeypot API.
Using Pydantic for validation - it catches bad data before it causes problems.
"""
from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict
from typing import List, Optional, Union


class Message(BaseModel):
    """A single message in the conversation.
    
    Notes:
    - Some external testers may omit `sender` in history items. We default to
      'scammer' to be permissive and avoid 422s for missing keys.
    - `sender` can be 'scammer' or 'agent' (we only act on 'scammer').
    - `timestamp` can be int (Unix millis) or str (ISO-8601); we convert to str.
    """
    model_config = ConfigDict(extra="ignore")  # ignore unexpected fields
    sender: Optional[str] = Field(default="scammer")  # default for leniency
    text: str
    timestamp: Optional[Union[str, int]] = None  # Accept both string and int
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def convert_timestamp(cls, v):
        """Convert numeric timestamps to string for consistency."""
        if isinstance(v, (int, float)):
            return str(int(v))
        return v


class Metadata(BaseModel):
    """Optional context about the message channel."""
    model_config = ConfigDict(extra="ignore")  # tolerate extra fields
    channel: str = "SMS"  # SMS, WhatsApp, Email, Chat
    language: str = "English"
    locale: str = "IN"


class HoneypotRequest(BaseModel):
    """
    Incoming scam message request.
    
    External systems or the frontend send suspected scam messages here
    for analysis and response. Each request has a sessionId to track
    multi-turn conversations with the same scammer.
    """
    model_config = ConfigDict(extra="ignore")  # tolerate extra fields from testers
    sessionId: str
    message: Message
    conversationHistory: List[Message] = Field(default_factory=list)
    metadata: Optional[Metadata] = None  # Optional contextual metadata
    timestamp: Optional[Union[str, int]] = None  # Some testers send timestamp at root level
    response_mode: Optional[str] = Field(default="rule_based", description="rule_based or llm")


class ExtractedIntelligence(BaseModel):
    """
    All the useful info we managed to extract from the scammer.
    This is what helps authorities track these guys down.
    """
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)


class EngagementMetrics(BaseModel):
    """How well did we keep the scammer talking?"""
    engagementDurationSeconds: int
    totalMessagesExchanged: int


class HoneypotResponse(BaseModel):
    """Enriched response format with metadata for UI."""
    status: str
    reply: str
    # Enriched fields for UI (optional, backward-compatible)
    reply_source: Optional[str] = None  # rule_based | llm | rule_based_fallback
    scam_detected: Optional[bool] = None
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    confidence: Optional[float] = None
    scam_type: Optional[str] = None
    scam_stage: Optional[str] = None
    stage_info: Optional[dict] = None  # Detailed stage: {stage, label, description, progress, ...}
    intelligence_counts: Optional[dict] = None
    callback_sent: Optional[bool] = None
    # v2.1 enrichment
    fraud_type: Optional[str] = None
    fraud_color: Optional[str] = None
    detection_reasons: Optional[List[str]] = None
    pattern_similarity: Optional[float] = None


class SimulationRequest(BaseModel):
    """Request to run an autonomous scam simulation."""
    scenario_id: str = Field(..., description="ID of the demo scenario to run")
    response_mode: str = Field(default="rule_based", description="rule_based or llm")


class SimulationResponse(BaseModel):
    """Full simulation result with conversation and analysis."""
    simulation_id: str
    scenario: dict
    conversation: List[dict]
    stage_progression: List[dict]
    final_analysis: dict
    total_messages: int
    response_mode: str


class CallbackPayload(BaseModel):
    """
    Payload for the government portal callback.
    We send this when we've gathered enough intel on a confirmed scam.
    """
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str
