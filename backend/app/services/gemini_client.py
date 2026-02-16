"""Gemini API client wrapper for LLM analysis."""
import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper for Google Gemini API with structured output support."""

    def __init__(self, api_key: str):
        """
        Initialize Gemini client with API key.

        Args:
            api_key: Google AI API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
        self.max_retries = 3
        self.base_delay = 10  # seconds (Gemini free tier resets per-minute)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate structured JSON response from Gemini.

        Args:
            system_prompt: System instruction for the model
            user_prompt: User message with stock data
            response_schema: Expected JSON schema for output

        Returns:
            Parsed JSON dict or None on failure

        Uses exponential backoff retry for 429/500 errors.
        """
        # Ensure event loop exists in background threads
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.3,
                    ),
                )

                # Parse JSON response
                result = response.text
                logger.info(f"Gemini API call successful (attempt {attempt + 1})")

                return json.loads(result)

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Gemini API error on attempt {attempt + 1}/{self.max_retries}: {error_msg}"
                )

                # Check if it's a retryable error (429 rate limit or 500 server error)
                is_retryable = (
                    "429" in error_msg or
                    "500" in error_msg or
                    "rate" in error_msg.lower() or
                    "quota" in error_msg.lower()
                )

                if is_retryable and attempt < self.max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    delay = self.base_delay * (2 ** attempt)
                    logger.info(f"Retrying after {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    # Non-retryable error or max retries exceeded
                    logger.error(f"Gemini API call failed: {error_msg}")
                    return None

        logger.error(f"Max retries ({self.max_retries}) exceeded for Gemini API call")
        return None
