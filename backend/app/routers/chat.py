"""AI chat assistant endpoint."""
import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.llm_client import LLMClient
from app.services.chat_service import chat_with_assistant
from app.services.chat_rate_limiter import chat_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=5000)


class ChatRequest(BaseModel):
    """Chat request with conversation history."""
    messages: List[ChatMessage] = Field(..., min_length=1, max_length=20)


class ChatResponse(BaseModel):
    """Chat response from AI assistant."""
    reply: str
    suggestions: List[str] = []


@router.get("/quota")
def get_chat_quota(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's chat quota info (read-only, no counter increment)."""
    tier = current_user.membership_tier if not current_user.is_admin else 'premium'
    quota = chat_rate_limiter.check_quota(str(current_user.id), tier)
    return {"tier": tier, **quota}


@router.post("", response_model=ChatResponse)
def send_chat_message(
    request: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Send a message to the AI assistant and get a response."""
    # Rate limit check with tier awareness
    tier = current_user.membership_tier if not current_user.is_admin else 'premium'
    allowed, reason, quota = chat_rate_limiter.check(str(current_user.id), tier)
    if not allowed:
        raise HTTPException(status_code=429, detail=reason)

    try:
        llm_client = LLMClient(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
        )

        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        reply, suggestions = chat_with_assistant(db, llm_client, messages)

        if not reply:
            raise HTTPException(status_code=502, detail="AI 服務暫時無法回應，請稍後再試")

        return ChatResponse(reply=reply, suggestions=suggestions)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="聊天服務發生錯誤")
