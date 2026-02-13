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

OUTPUT FORMAT:
- Return ONLY the rephrased reply text, nothing else
- Do NOT include any prefix like "Here is...", "Sure...", "Rephrased:", etc.
- Do NOT include quotation marks around the reply
- Do NOT add explanations, notes, or commentary

You receive:
- Strategy: The engagement strategy chosen by the rule engine
- Original Reply: The rule-based reply to rephrase
- Last Scammer Message: Context of what the scammer said"""


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
