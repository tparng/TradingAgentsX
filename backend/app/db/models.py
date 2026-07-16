"""
Database models for users, settings, and reports
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class User(Base):
    """User model for storing Google OAuth users"""
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    settings: Mapped[Optional["UserSettings"]] = relationship(
        "UserSettings", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", 
        back_populates="user",
        cascade="all, delete-orphan"
    )


class UserSettings(Base):
    """User settings (encrypted API keys, custom base URLs)"""
    __tablename__ = "user_settings"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True,
        nullable=False
    )
    # Store settings as encrypted JSON string
    encrypted_settings: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="settings")


class Report(Base):
    """Analysis report storage"""
    __tablename__ = "reports"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    market_type: Mapped[str] = mapped_column(String(10), nullable=False)  # us, twse, tpex
    analysis_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    # Store full result as JSONB
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        index=True
    )
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="reports")


class WatchlistItem(Base):
    """Single-owner watchlist — tickers to track and auto-analyze."""
    __tablename__ = "watchlist"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    market_type: Mapped[str] = mapped_column(String(10), nullable=False, default="us")
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_recommendation: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    last_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class WatchlistCandidate(Base):
    """Auto-generated stock candidates from screener + LLM ranking."""
    __tablename__ = "watchlist_candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    market_type: Mapped[str] = mapped_column(String(10), nullable=False, default="us")
    price_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rsi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    signal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # BULLISH/BEARISH/NEUTRAL
    screened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending/added/dismissed
