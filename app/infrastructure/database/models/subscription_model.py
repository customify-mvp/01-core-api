"""
SubscriptionModel - SQLAlchemy model for subscriptions table.

Represents user subscription plans and usage tracking.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.session import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.user_model import UserModel


class SubscriptionModel(Base):
    """
    SQLAlchemy model for subscriptions table.
    
    Tracks user subscription plans, Stripe integration, and monthly usage.
    Uses SQLAlchemy 2.0 style with Mapped[T] type hints.
    """
    
    __tablename__ = "subscriptions"
    
    # ============================================================
    # Columns (SQLAlchemy 2.0 style)
    # ============================================================
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="free"
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="active"
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255))
    designs_this_month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # ============================================================
    # Relationships (SQLAlchemy 2.0 style)
    # ============================================================
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="subscription",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<SubscriptionModel(id={self.id}, user_id={self.user_id}, plan={self.plan}, status={self.status})>"
