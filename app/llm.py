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
    """Gemini integration with strict timeout and auto-fallback."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.timeout_ms = int(os.getenv("LLM_TIMEOUT_MS", "5000"))  # Increased timeout
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # Valid model name
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
            "genai_installed": GENAI_AVAILABLE,
            "api_key_set": bool(self.api_key)
        }


# Singleton
llm_service = LLMService()
