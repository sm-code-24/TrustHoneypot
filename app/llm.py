"""
LLM Integration - Groq (Llama 3.3 70B) for reply phrasing ONLY.

ARCHITECTURAL INVARIANT:
"LLM enhances realism, NEVER correctness."

The LLM is used ONLY to rephrase rule-based agent replies.
It NEVER:
- detects scams
- changes risk scores
- extracts intelligence
- triggers callbacks
- asks for OTP / passwords / credentials
"""
import os
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load .env from repo root (parent of app/) or current dir
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv()

logger = logging.getLogger(__name__)

# httpx for async REST API calls
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not installed. LLM features disabled.")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ─── Greeting Detection ───────────────────────────────────────────────────────

# Common greeting phrases in English, Hindi, and Hinglish
# Used to identify when a scammer is just starting the conversation with a simple greeting
_GREETING_PHRASES = [
    "hi", "hello", "hey", "hii", "hiii", "helo", "helo",
    "good morning", "good afternoon", "good evening", "good night",
    "gm", "gn", "morning", "evening",
    "namaste", "namaskar", "namaskaaram",
    "hello sir", "hello madam", "hello ji", "hi sir", "hi ji",
    "hey there", "hey sir", "hey ji",
    "haan ji", "ji", "haanji",
    "howdy", "greetings", "sup", "yo",
]

# Keywords that indicate scam/fraud intent
# If these appear in a message, it's NOT just a greeting
_SCAM_KEYWORDS = [
    "account", "bank", "verify", "kyc", "suspend", "block", "urgent",
    "payment", "pay", "upi", "otp", "pin", "password", "refund",
    "prize", "lottery", "won", "winner", "reward", "cashback",
    "police", "arrest", "court", "case", "warrant", "cbi", "fir",
    "parcel", "courier", "drugs", "customs",
    "transfer", "send money", "bhejo", "paisa",
    "aadhaar", "pan card", "sim", "deactivate",
    "video call", "digital arrest", "stay on call",
    "investment", "trading", "profit", "guaranteed returns",
    "job", "work from home", "registration fee",
]


def is_greeting_message(text: str) -> bool:
    """Detect if message is a simple greeting with no scam indicators.

    This function identifies the initial greeting stage of a scam attempt,
    where the scammer is just trying to establish contact before launching
    their actual scam pitch.

    Conditions for a message to be classified as a greeting:
    - Message contains a common greeting phrase
    - Message length <= 4 words (keeps it simple)
    - No scam-related keywords present
    - No urgency/payment/verification indicators

    Examples:
        - "hi" → True
        - "hello sir" → True
        - "good morning" → True
        - "namaste ji" → True
        - "hi verify your account" → False (has scam keyword)
        - "hello i am calling from bank regarding your kyc" → False (too long + scam keywords)
    """
    cleaned = text.strip().lower().rstrip(".,!?;:'\"")
    words = cleaned.split()

    # Reject messages that are too long (likely scam pitch, not just greeting)
    if len(words) > 4:
        return False

    # Check for scam keywords — reject immediately if found
    # This prevents "hi your account is suspended" from being treated as greeting
    for kw in _SCAM_KEYWORDS:
        if kw in cleaned:
            return False

    # Check if the message contains a greeting phrase
    # We match exact, prefix, or suffix to handle punctuation and spacing
    for phrase in _GREETING_PHRASES:
        if cleaned == phrase or cleaned.startswith(phrase + " ") or cleaned.endswith(" " + phrase):
            return True
        # Also match if the whole message is just the greeting with minor variations
        if phrase in cleaned and len(words) <= 3:
            return True

    return False


# ─── Greeting-Stage LLM Prompt ────────────────────────────────────────────────

GREETING_LLM_PROMPT = """You are a cautious but polite person who has just received a greeting message from an unknown sender. Respond naturally and politely. Do not escalate. Do not mention scams. Keep it short and human-like. Slightly cautious but friendly.

STRICT RULES:
1. Respond in 1-2 sentences MAXIMUM
2. Do NOT be defensive or suspicious
3. Do NOT mention scams, fraud, or anything negative
4. Do NOT ask verification questions
5. Sound like a normal, slightly cautious Indian person
6. Be warm but not overly enthusiastic
7. If the greeting is in Hindi/Hinglish, respond in casual Hinglish (Roman script)
8. If the greeting is in English, respond in simple English

Examples of GOOD responses:
- "Hello! Yes, who is this?"
- "Hi ji, haan bolo?"
- "Good morning! Kaun bol raha hai?"
- "Hello, yes I'm here. Who is this?"
- "Namaste ji, bataiye?"

Examples of BAD responses (NEVER do this):
- "What do you want? I don't trust unknown callers."
- "Is this a scam? Who are you?"
- "I'm not sure what this is about. Can you explain from the beginning?"

OUTPUT FORMAT:
- Return ONLY the response text, nothing else
- Do NOT include any prefix like "Here is...", "Sure...", etc.
- Do NOT include quotation marks around the reply
- Do NOT add explanations, notes, or commentary"""

# Greeting fallback responses (used when LLM times out during greeting stage)
GREETING_FALLBACK_RESPONSES = [
    "Hello! Ji, kaun bol raha hai?",
    "Hi! Yes, who is this?",
    "Hello ji, haan bataiye?",
    "Hi, yes I'm here. Who is this?",
    "Namaste! Ji bolo?",
    "Hello! Haan ji, bolo bolo.",
    "Hi ji! Kahiye, kaun hai?",
    "Good day! Yes, who is calling?",
]

# Strict system prompt
SYSTEM_PROMPT = """You are rephrasing a scam honeypot agent's reply to sound more natural and human-like.
The agent is pretending to be a vulnerable Indian citizen (typically elderly) to keep a scammer engaged.

STRICT RULES:
1. Never reveal that you know it's a scam
2. Never ask for OTP, PIN, password, CVV, or any credentials
3. Never impersonate police, government, or bank officials
4. Keep replies short (1-3 sentences max)
5. Sound like a confused, elderly Indian person
6. LANGUAGE MATCHING (CRITICAL):
   - If the Original Reply is in Hindi/Hinglish → respond ONLY in Hindi/Hinglish
   - If the Original Reply is in English → respond in English (light Hindi words like "ji", "beta" are OK)
   - If the Scammer Message is in Hindi but the reply is English, still follow the reply's language
7. Stay cautious but not suspicious
8. Match the emotional tone of the strategy given
9. Do NOT add any new information not in the original reply
10. Do NOT change the intent or strategy of the reply
11. HINDI STYLE GUIDE:
    - Use Roman Hindi (Hinglish), NOT Devanagari script
    - Write how Indians actually text: "Haan ji", "Kya baat hai", "Ek minute ruko"
    - Mix natural filler words: "ji", "beta", "haan", "arey", "matlab"
    - Keep grammar casual — don't write textbook Hindi
    - Example inputs/outputs:
      Input (Hindi reply): "Haan ji, mujhe samajh nahi aa raha. Thoda time dijiye."
      Output: "Arey haan ji, ye sab samajh mein nahi aa raha mujhe... thoda time do na beta."
      Input (English reply): "Please wait, I am trying to understand."
      Output: "Wait wait, I am trying to understand ji... this technology is confusing."
12. ANTI-REPETITION (v2.2):
    - You will receive "Recent Turns" showing the last few messages exchanged.
    - NEVER repeat or closely mirror phrasing from the Recent Turns.
    - Vary sentence openers, filler words, and question structures each time.
    - If the Original Reply uses the same words as a recent turn, rephrase MORE aggressively.
13. STAGE-AWARE TONE (v2.2):
    - The Strategy field tells you the engagement stage.
    - "greeting_rapport" → warm, casual, no suspicion at all
    - "initial_confusion" / "stalling_confused" → genuinely confused, asking questions
    - "curious_but_cautious" → slightly wary, probing for details
    - "fearful_compliance" → scared, trembling, but slowly cooperating
    - "detail_seeking_extraction" → worried but trying to help, asking for specifics

OUTPUT FORMAT:
- Return ONLY the rephrased reply text, nothing else
- Do NOT include any prefix like "Here is...", "Sure...", "Rephrased:", etc.
- Do NOT include quotation marks around the reply
- Do NOT add explanations, notes, or commentary

You receive:
- Strategy: The engagement strategy chosen by the rule engine
- Original Reply: The rule-based reply to rephrase
- Last Scammer Message: Context of what the scammer said
- Recent Turns: Last few conversation exchanges for anti-repetition context"""


class LLMService:
    """Groq LLM integration with async httpx, strict timeout and auto-fallback."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.timeout_ms = int(os.getenv("LLM_TIMEOUT_MS", "8000"))
        self.enabled = False
        self._client: Optional[httpx.AsyncClient] = None
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5
        self._backoff_until = 0.0
        self._total_calls = 0
        self._total_successes = 0
        self._total_fallbacks = 0
        self._avg_latency_ms = 0.0
        self._configure()

    def _configure(self):
        """Configure async httpx client for Groq REST API."""
        logger.info(f"🤖 LLM INIT: httpx_available={HTTPX_AVAILABLE}, api_key_set={bool(self.api_key)}, api_key_len={len(self.api_key)}, model={self.model_name}")
        if not HTTPX_AVAILABLE:
            logger.warning("🤖 LLM service DISABLED: httpx not installed. Install with: pip install httpx")
            return
        if not self.api_key:
            logger.warning("🤖 LLM service DISABLED: GROQ_API_KEY not set in environment variables")
            return
        try:
            transport = httpx.AsyncHTTPTransport(
                retries=1,
                local_address="0.0.0.0",
            )
            self._client = httpx.AsyncClient(
                transport=transport,
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=self.timeout_ms / 1000.0,
                    write=5.0,
                    pool=5.0,
                ),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
            self.enabled = True
            logger.info(f"🤖 LLM service ENABLED: model={self.model_name}, timeout={self.timeout_ms}ms (Groq REST via httpx)")
        except Exception as e:
            logger.error(f"🤖 LLM service FAILED to configure: {e}", exc_info=True)
            self.enabled = False

    async def generate_greeting_reply(
        self,
        scammer_message: str
    ) -> Tuple[str, str]:
        """
        Generate a natural greeting response using the dedicated GREETING_LLM_PROMPT.

        This method is called when we detect a greeting-stage message (e.g., "hi", "hello").
        It uses a specialized prompt that instructs the LLM to respond warmly but cautiously,
        without being defensive or mentioning scams.

        Args:
            scammer_message: The greeting message from the scammer (e.g., "hello sir")

        Returns:
            Tuple of (final_reply, source) where:
            - final_reply: The generated greeting response
            - source: "llm" (successful LLM call), "rule_based" (LLM disabled), 
                     or "rule_based_fallback" (LLM failed/timeout)

        Examples:
            Input: "hi"
            Output: ("Hello! Who is this?", "llm")
        
            Input: "good morning"
            Output: ("Good morning ji! Kaun bol rahe ho?", "llm")
        """
        import random as _random

        # If LLM service is disabled, use rule-based fallback immediately
        if not self.enabled:
            logger.warning("🤖 LLM SKIP (greeting): service not enabled")
            return _random.choice(GREETING_FALLBACK_RESPONSES), "rule_based"

        # Circuit breaker check — if we've had too many failures, skip LLM temporarily
        now = time.time()
        if now < self._backoff_until:
            logger.debug("LLM circuit breaker active during greeting, using fallback")
            return _random.choice(GREETING_FALLBACK_RESPONSES), "rule_based_fallback"

        self._total_calls += 1
        start_time = time.time()

        try:
            # Construct the prompt for the LLM
            # The GREETING_LLM_PROMPT already contains detailed instructions,
            # we just need to provide the actual greeting message
            prompt = f"Greeting received: {scammer_message}\n\nRespond naturally:"

            # Call the LLM with timeout protection
            llm_reply = await asyncio.wait_for(
                self._generate_with_prompt(GREETING_LLM_PROMPT, prompt),
                timeout=self.timeout_ms / 1000.0
            )

            elapsed_ms = (time.time() - start_time) * 1000

            # Validate the response — ensure it's not empty and passes safety checks
            if llm_reply and self._is_safe(llm_reply):
                # Success — update metrics and return LLM response
                self._consecutive_failures = 0
                self._total_successes += 1
                self._avg_latency_ms = (
                    (self._avg_latency_ms * (self._total_successes - 1) + elapsed_ms)
                    / self._total_successes
                )
                logger.info(f"LLM greeting reply generated in {elapsed_ms:.0f}ms")
                return llm_reply.strip(), "llm"
            else:
                # Response was unsafe or empty — fall back to rule-based greeting
                self._record_failure("unsafe_or_empty_greeting")
                logger.warning(f"LLM greeting reply unsafe or empty, falling back. elapsed={elapsed_ms:.0f}ms")
                return _random.choice(GREETING_FALLBACK_RESPONSES), "rule_based_fallback"

        except asyncio.TimeoutError:
            # LLM took too long to respond — use fallback greeting
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_failure("timeout_greeting")
            logger.warning(f"LLM greeting timeout after {elapsed_ms:.0f}ms, falling back to greeting fallback")
            return _random.choice(GREETING_FALLBACK_RESPONSES), "rule_based_fallback"
        except Exception as e:
            # Any other error — log and fall back to rule-based greeting
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_failure("error_greeting")
            logger.error(f"LLM greeting error after {elapsed_ms:.0f}ms: {e}")
            return _random.choice(GREETING_FALLBACK_RESPONSES), "rule_based_fallback"

    async def rephrase_reply(
        self,
        strategy: str,
        rule_reply: str,
        scammer_message: str,
        recent_turns: Optional[list] = None
    ) -> Tuple[str, str]:
        """
        Rephrase a rule-based reply using LLM.

        Args:
            strategy: The engagement strategy label (e.g. "initial_confusion")
            rule_reply: The rule-based reply text to rephrase
            scammer_message: The last scammer message for context
            recent_turns: Optional list of recent conversation dicts [{role, text}]
                          Used for anti-repetition (v2.2)

        Returns:
            (final_reply, source) where source is "llm" | "rule_based" | "rule_based_fallback"
        """
        if not self.enabled:
            logger.warning(f"🤖 LLM SKIP: service not enabled (api_key_set={bool(self.api_key)}, httpx={HTTPX_AVAILABLE})")
            return rule_reply, "rule_based"

        # Circuit breaker: skip calls during backoff
        now = time.time()
        if now < self._backoff_until:
            remaining = self._backoff_until - now
            logger.debug(f"LLM circuit breaker active, skipping call ({remaining:.0f}s remaining)")
            return rule_reply, "rule_based_fallback"

        self._total_calls += 1
        start_time = time.time()

        try:
            # Build recent turns context for anti-repetition (v2.2)
            turns_str = ""
            if recent_turns:
                last_turns = recent_turns[-6:]  # last 3 exchanges (6 messages)
                turns_lines = []
                for t in last_turns:
                    role_label = "Agent" if t.get("role") == "agent" else "Scammer"
                    turns_lines.append(f"  {role_label}: {t.get('text', '')}")
                turns_str = "\n".join(turns_lines)

            prompt = (
                f"Strategy: {strategy}\n"
                f"Original Reply: {rule_reply}\n"
                f"Last Scammer Message: {scammer_message}\n"
            )
            if turns_str:
                prompt += f"Recent Turns:\n{turns_str}\n"
            prompt += "\nRephrase the Original Reply naturally:"

            llm_reply = await asyncio.wait_for(
                self._generate(prompt),
                timeout=self.timeout_ms / 1000.0
            )

            elapsed_ms = (time.time() - start_time) * 1000

            if llm_reply and self._is_safe(llm_reply):
                self._consecutive_failures = 0
                self._total_successes += 1
                self._avg_latency_ms = (
                    (self._avg_latency_ms * (self._total_successes - 1) + elapsed_ms)
                    / self._total_successes
                )
                logger.info(f"LLM reply generated in {elapsed_ms:.0f}ms")
                return llm_reply.strip(), "llm"
            else:
                self._record_failure("unsafe_or_empty")
                logger.warning(f"LLM reply unsafe or empty, falling back. elapsed={elapsed_ms:.0f}ms")
                return rule_reply, "rule_based_fallback"

        except asyncio.TimeoutError:
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_failure("timeout")
            logger.warning(f"LLM timeout after {elapsed_ms:.0f}ms, falling back to rule-based")
            return rule_reply, "rule_based_fallback"
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self._record_failure("error")
            logger.error(f"LLM error after {elapsed_ms:.0f}ms: {e}")
            return rule_reply, "rule_based_fallback"

    def _record_failure(self, reason: str):
        """Track failures and activate circuit breaker if needed."""
        self._consecutive_failures += 1
        self._total_fallbacks += 1
        if self._consecutive_failures >= self._max_consecutive_failures:
            backoff_seconds = min(60, 10 * (self._consecutive_failures // self._max_consecutive_failures))
            self._backoff_until = time.time() + backoff_seconds
            logger.warning(
                f"LLM circuit breaker activated: {self._consecutive_failures} consecutive failures "
                f"(reason: {reason}), backing off for {backoff_seconds}s"
            )

    async def _generate_with_prompt(self, system_prompt: str, prompt: str) -> Optional[str]:
        """Call Groq API with a custom system prompt."""
        if not self._client:
            return None

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 80,
            "temperature": 0.7,
            "top_p": 0.9,
        }

        return await self._call_groq(payload)

    async def _generate(self, prompt: str) -> Optional[str]:
        """Call Groq API (OpenAI-compatible) with async httpx."""
        if not self._client:
            return None

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 150,
            "temperature": 0.7,
            "top_p": 0.9,
        }

        return await self._call_groq(payload)

    async def _call_groq(self, payload: dict) -> Optional[str]:
        """Execute Groq API call with error handling."""
        if not self._client:
            return None

        try:
            response = await self._client.post(GROQ_API_URL, json=payload)

            if response.status_code == 429:
                retry_delay = 30
                retry_after = response.headers.get("retry-after")
                if retry_after:
                    try:
                        retry_delay = int(float(retry_after))
                    except ValueError:
                        pass
                self._backoff_until = time.time() + retry_delay
                logger.warning(f"Groq rate limited (429), backing off for {retry_delay}s")
                return None

            if response.status_code != 200:
                error_msg = response.text[:200]
                logger.error(f"Groq API error {response.status_code}: {error_msg}")
                return None

            data = response.json()
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content")
                if content:
                    return content

            logger.warning("Groq returned empty response")
            return None

        except httpx.TimeoutException as e:
            logger.warning(f"Groq request timeout: {e}")
            return None
        except httpx.ConnectError as e:
            logger.error(f"Groq connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            return None

    def _is_safe(self, reply: str) -> bool:
        """Check if LLM reply is safe to send."""
        lower = reply.lower()
        # Phrases that reveal scam awareness or impersonate authority
        unsafe_phrases = [
            "share your otp", "tell me your otp", "enter your otp",
            "tell me your pin", "enter your password", "share your password",
            "send me your cvv", "your pin number",
            "i know this is a scam", "this is fraud", "you are a scammer",
            "you are fraud", "i know you are fake",
            "i am officer", "i am inspector", "i am from cbi",
            "i am from police", "i am from cyber cell",
            "main police se hoon", "main officer hoon", "main cbi se hoon",
            "hum police hain", "cyber crime cell se",
            "otp batao", "otp bhejo", "pin batao", "password bhejo",
        ]
        for phrase in unsafe_phrases:
            if phrase in lower:
                logger.warning(f"Unsafe LLM output detected: contains '{phrase}'")
                return False
        return True

    def get_status(self) -> dict:
        """Return LLM service status for UI."""
        return {
            "available": self.enabled,
            "model": self.model_name if self.enabled else None,
            "timeout_ms": self.timeout_ms,
            "httpx_installed": HTTPX_AVAILABLE,
            "api_key_set": bool(self.api_key),
            "circuit_breaker": "active" if time.time() < self._backoff_until else "idle",
            "stats": {
                "total_calls": self._total_calls,
                "successes": self._total_successes,
                "fallbacks": self._total_fallbacks,
                "avg_latency_ms": round(self._avg_latency_ms, 1),
                "consecutive_failures": self._consecutive_failures,
            }
        }

    async def close(self):
        """Clean up httpx client on shutdown."""
        if self._client:
            await self._client.aclose()
            logger.info("LLM httpx client closed")


# Singleton
llm_service = LLMService()
