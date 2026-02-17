"""OpenAI-compatible LLM client for stock analysis (Apertis AI / Claude)."""
import json
import logging
import time
from typing import Optional, Dict, Any

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper for OpenAI-compatible API with structured JSON output."""

    def __init__(self, api_key: str, base_url: str, model: str):
        """
        Initialize LLM client.

        Args:
            api_key: API key for the service
            base_url: Base URL (e.g., https://api.apertis.ai/v1)
            model: Model identifier (e.g., claude-opus-4-6)
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_retries = 3
        self.base_delay = 5

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate structured JSON response from LLM.

        Args:
            system_prompt: System instruction for the model
            user_prompt: User message with stock data
            response_schema: Expected JSON schema for output

        Returns:
            Parsed JSON dict or None on failure
        """
        # Build schema description for the prompt
        schema_fields = response_schema.get("properties", {})
        schema_desc = "\n".join(
            f'- "{k}": {v.get("description", v.get("type", "string"))}'
            for k, v in schema_fields.items()
        )
        required = response_schema.get("required", [])

        json_instruction = (
            f"\n\n請以 JSON 格式回覆，必須包含以下欄位：\n{schema_desc}\n"
            f"必填欄位: {required}\n"
            "每個欄位限制在 150 字以內，risk_alerts 最多 3 項。\n"
            "回覆僅包含 JSON，不要加上其他文字或 markdown code fence。"
        )

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt + json_instruction},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=8192,
                )

                finish_reason = response.choices[0].finish_reason
                content = response.choices[0].message.content
                if not content:
                    logger.warning(f"LLM returned empty content (attempt {attempt + 1}), finish_reason={finish_reason}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.base_delay)
                        continue
                    return None

                raw = content.strip()
                logger.info(f"LLM API call successful (attempt {attempt + 1}), len={len(raw)}, finish_reason={finish_reason}")

                # Detect truncated response
                if finish_reason == 'length':
                    logger.warning(f"Response truncated (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        # Retry with shorter instruction
                        user_prompt = user_prompt + "\n\n[重要] 回覆被截斷，請大幅精簡每個欄位，每欄位最多 80 字。"
                        time.sleep(self.base_delay)
                        continue
                    return None

                # Strip markdown code fence if present
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                    if raw.endswith("```"):
                        raw = raw[:-3].strip()

                return json.loads(raw)

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.base_delay)
                    continue
                logger.error(f"LLM response not valid JSON after {self.max_retries} attempts")
                return None

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"LLM API error on attempt {attempt + 1}/{self.max_retries}: {error_msg}"
                )

                is_retryable = (
                    "429" in error_msg or
                    "500" in error_msg or
                    "502" in error_msg or
                    "503" in error_msg or
                    "rate" in error_msg.lower() or
                    "timeout" in error_msg.lower()
                )

                if is_retryable and attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.info(f"Retrying after {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"LLM API call failed: {error_msg}")
                    return None

        logger.error(f"Max retries ({self.max_retries}) exceeded for LLM API call")
        return None
