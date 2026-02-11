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

# Try to import google genai (new SDK)
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed. LLM features disabled.")


# Strict system prompt
SYSTEM_PROMPT = """You are rephrasing a scam honeypot agent's reply to sound more natural and human-like.

STRICT RULES:
1. Never reveal that you know it's a scam
2. Never ask for OTP, PIN, password, CVV, or any credentials
3. Never impersonate police, government, or bank officials
4. Keep replies short (1-3 sentences max)
5. Sound like a confused, elderly Indian person
6. Use simple language, mix Hindi-English naturally
7. Stay cautious but not suspicious
8. Match the emotional tone of the strategy given
9. Do NOT add any new information not in the original reply
10. Do NOT change the intent or strategy of the reply

You receive:
- Strategy: The engagement strategy chosen by the rule engine
- Original Reply: The rule-based reply to rephrase
- Last Scammer Message: Context of what the scammer said

Return ONLY the rephrased reply. Nothing else."""


class LLMService:
    """Gemini integration with strict timeout and auto-fallback."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.timeout_ms = int(os.getenv("LLM_TIMEOUT_MS", "3000"))
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
        self.enabled = False
        self.client = None
        self._configure()
    
    def _configure(self):
        """Configure Gemini client using google-genai SDK."""
        if not GENAI_AVAILABLE:
            logger.info("LLM service disabled: google-genai not installed")
            return
        if not self.api_key:
            logger.info("LLM service disabled: GEMINI_API_KEY not set")
            return
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.enabled = True
            logger.info(f"LLM service configured: model={self.model_name}, timeout={self.timeout_ms}ms")
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {e}")
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
        
        start_time = time.time()
        
        try:
            prompt = (
                f"Strategy: {strategy}\n"
                f"Original Reply: {rule_reply}\n"
                f"Last Scammer Message: {scammer_message}\n\n"
                f"Rephrase the Original Reply naturally:"
            )
            
            # Run with timeout
            llm_reply = await asyncio.wait_for(
                self._generate(prompt),
                timeout=self.timeout_ms / 1000.0
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if llm_reply and self._is_safe(llm_reply):
                logger.info(f"LLM reply generated in {elapsed_ms:.0f}ms")
                return llm_reply.strip(), "llm"
            else:
                logger.warning(f"LLM reply unsafe or empty, falling back. elapsed={elapsed_ms:.0f}ms")
                return rule_reply, "rule_based_fallback"
                
        except asyncio.TimeoutError:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.warning(f"LLM timeout after {elapsed_ms:.0f}ms, falling back to rule-based")
            return rule_reply, "rule_based_fallback"
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"LLM error after {elapsed_ms:.0f}ms: {e}")
            return rule_reply, "rule_based_fallback"
    
    async def _generate(self, prompt: str) -> Optional[str]:
        """Call Gemini API asynchronously using google-genai SDK."""
        loop = asyncio.get_running_loop()
        
        def _sync_generate():
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                ),
            ]
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            )
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
                if response and hasattr(response, 'text') and response.text:
                    return response.text
                # Fallback: try to extract from candidates
                if response and response.candidates:
                    for candidate in response.candidates:
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    return part.text
                logger.warning("Gemini returned empty/blocked response")
                return None
            except Exception as e:
                logger.error(f"Gemini generate_content error: {e}")
                return None
        
        return await loop.run_in_executor(None, _sync_generate)
    
    def _is_safe(self, reply: str) -> bool:
        """Check if LLM reply is safe to send."""
        lower = reply.lower()
        unsafe_patterns = [
            "otp", "pin number", "cvv", "password", "credential",
            "i know this is a scam", "this is fraud", "you are a scammer",
            "police", "i am officer", "i am from", "cbi", "cyber cell",
            "share your otp", "tell me your pin", "enter your password"
        ]
        for pattern in unsafe_patterns:
            if pattern in lower:
                logger.warning(f"Unsafe LLM output detected: contains '{pattern}'")
                return False
        return True
    
    def get_status(self) -> dict:
        """Return LLM service status for UI."""
        return {
            "available": self.enabled,
            "model": self.model_name if self.enabled else None,
            "timeout_ms": self.timeout_ms,
            "genai_installed": GENAI_AVAILABLE,
            "api_key_set": bool(self.api_key)
        }


# Singleton
llm_service = LLMService()
