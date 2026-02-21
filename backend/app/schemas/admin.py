"""Admin management schemas."""
from pydantic import BaseModel, field_validator


class TierUpdateRequest(BaseModel):
    """Request to update a user's membership tier."""

    membership_tier: str

    @field_validator('membership_tier')
    @classmethod
    def valid_tier(cls, v: str) -> str:
        if v not in ('free', 'premium'):
            raise ValueError('tier 必須為 free 或 premium')
        return v
