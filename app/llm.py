"""
LLM Integration - Gemini for reply phrasing ONLY.

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
import json
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

# httpx for direct REST API calls (avoids google-genai SDK IPv6 issues)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not installed. LLM features disabled.")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

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

You receive:
- Strategy: The engagement strategy chosen by the rule engine
- Original Reply: The rule-based reply to rephrase
- Last Scammer Message: Context of what the scammer said

Return ONLY the rephrased reply. Nothing else."""


class LLMService:
    """Gemini REST API integration with async httpx, strict timeout and auto-fallback."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.timeout_ms = int(os.getenv("LLM_TIMEOUT_MS", "8000"))
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.enabled = False
        self._client: Optional[httpx.AsyncClient] = None
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5
        self._backoff_until = 0.0  # timestamp until which we skip LLM calls
        self._total_calls = 0
        self._total_successes = 0
        self._total_fallbacks = 0
        self._avg_latency_ms = 0.0
        self._configure()

    def _configure(self):
        """Configure async httpx client for Gemini REST API."""
        if not HTTPX_AVAILABLE:
            logger.info("LLM service disabled: httpx not installed")
            return
        if not self.api_key:
            logger.info("LLM service disabled: GEMINI_API_KEY not set")
            return
        try:
            # Force IPv4 via custom transport to avoid IPv6 hanging on Windows
            transport = httpx.AsyncHTTPTransport(
                retries=1,
                local_address="0.0.0.0",  # Forces IPv4
            )
            self._client = httpx.AsyncClient(
                transport=transport,
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=self.timeout_ms / 1000.0,
                    write=5.0,
                    pool=5.0,
                ),
                headers={"Content-Type": "application/json"},
            )
            self.enabled = True
            logger.info(f"LLM service configured: model={self.model_name}, timeout={self.timeout_ms}ms (REST API, IPv4)")
        except Exception as e:
            logger.error(f"Failed to configure LLM client: {e}")
            self.enabled = False

    async def rephrase_reply(
        self,
        strategy: str,
        rule_reply: str,
        scammer_message: str
    ) -> Tuple[str, str]:
        """
        Rephrase a rule-based reply using LLM.

        Returns:
            (final_reply, source) where source is "llm" | "rule_based" | "rule_based_fallback"
        """
        if not self.enabled:
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
            prompt = (
                f"Strategy: {strategy}\n"
                f"Original Reply: {rule_reply}\n"
                f"Last Scammer Message: {scammer_message}\n\n"
                f"Rephrase the Original Reply naturally:"
            )

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

    async def _generate(self, prompt: str) -> Optional[str]:
        """Call Gemini REST API directly with async httpx (IPv4, proper timeouts)."""
        if not self._client:
            return None

        url = f"{GEMINI_API_BASE}/models/{self.model_name}:generateContent"

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 150,
                "temperature": 0.7,
                "topP": 0.9,
            }
        }

        try:
            response = await self._client.post(
                url,
                params={"key": self.api_key},
                json=payload,
            )

            if response.status_code == 429:
                # Rate limited — extract retry delay if available
                error_data = response.json()
                retry_delay = 30  # default
                details = error_data.get("error", {}).get("details", [])
                for d in details:
                    if d.get("@type", "").endswith("RetryInfo"):
                        delay_str = d.get("retryDelay", "30s").rstrip("s")
                        try:
                            retry_delay = int(float(delay_str))
                        except ValueError:
                            pass
                self._backoff_until = time.time() + retry_delay
                logger.warning(f"LLM rate limited (429), backing off for {retry_delay}s")
                return None

            if response.status_code != 200:
                error_msg = response.text[:200]
                logger.error(f"Gemini API error {response.status_code}: {error_msg}")
                return None

            data = response.json()

            # Extract text from response
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"]

            # Check for blocked response
            block_reason = data.get("promptFeedback", {}).get("blockReason")
            if block_reason:
                logger.warning(f"Gemini blocked response: {block_reason}")
            else:
                logger.warning("Gemini returned empty response")
            return None

        except httpx.TimeoutException as e:
            logger.warning(f"Gemini request timeout: {e}")
            return None
        except httpx.ConnectError as e:
            logger.error(f"Gemini connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
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
