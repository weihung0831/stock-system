"""Sector tag CRUD endpoints."""
import logging
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.sector_tag import SectorTag
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sector-tags", tags=["sector-tags"])


# --- Schemas ---

class SectorTagCreate(BaseModel):
    name: str = Field(..., max_length=20)
    color: str = Field(default="#9ca3af", max_length=7)
    keywords: str = Field(default="", max_length=200)
    sort_order: int = Field(default=0)


class SectorTagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=20)
    color: Optional[str] = Field(default=None, max_length=7)
    keywords: Optional[str] = Field(default=None, max_length=200)
    sort_order: Optional[int] = None


class SectorTagResponse(BaseModel):
    id: int
    name: str
    color: str
    keywords: str
    sort_order: int

    class Config:
        from_attributes = True


# --- Endpoints ---

@router.get("", response_model=List[SectorTagResponse])
def list_sector_tags(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get all sector tags ordered by sort_order."""
    return db.query(SectorTag).order_by(SectorTag.sort_order, SectorTag.id).all()


@router.post("", response_model=SectorTagResponse, status_code=status.HTTP_201_CREATED)
def create_sector_tag(
    body: SectorTagCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new sector tag."""
    existing = db.query(SectorTag).filter(SectorTag.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"標籤 '{body.name}' 已存在")

    tag = SectorTag(**body.dict())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=SectorTagResponse)
def update_sector_tag(
    tag_id: int,
    body: SectorTagUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a sector tag."""
    tag = db.query(SectorTag).filter(SectorTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="標籤不存在")

    update_data = body.dict(exclude_unset=True)
    # Check name uniqueness if changing name
    if "name" in update_data:
        dup = db.query(SectorTag).filter(
            SectorTag.name == update_data["name"],
            SectorTag.id != tag_id
        ).first()
        if dup:
            raise HTTPException(status_code=400, detail=f"標籤 '{update_data['name']}' 已存在")

    for key, value in update_data.items():
        setattr(tag, key, value)

    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sector_tag(
    tag_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a sector tag."""
    tag = db.query(SectorTag).filter(SectorTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="標籤不存在")

    db.delete(tag)
    db.commit()


@router.post("/seed", response_model=List[SectorTagResponse])
def seed_default_tags(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Seed default sector tags if table is empty."""
    count = db.query(SectorTag).count()
    if count > 0:
        return db.query(SectorTag).order_by(SectorTag.sort_order).all()

    defaults = [
        SectorTag(name="半導體", color="#3b82f6", keywords="半導體", sort_order=1),
        SectorTag(name="電子", color="#22c55e", keywords="電子", sort_order=2),
        SectorTag(name="金融", color="#eab308", keywords="金融", sort_order=3),
        SectorTag(name="傳產", color="#6b7280", keywords="傳產", sort_order=4),
    ]
    db.add_all(defaults)
    db.commit()
    return db.query(SectorTag).order_by(SectorTag.sort_order).all()
