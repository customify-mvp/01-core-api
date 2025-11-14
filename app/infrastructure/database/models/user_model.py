"""
UserModel - SQLAlchemy model for users table.

Represents application users (merchants).
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.session import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.subscription_model import SubscriptionModel
    from app.infrastructure.database.models.design_model import DesignModel
    from app.infrastructure.database.models.order_model import OrderModel
    from app.infrastructure.database.models.shopify_store_model import ShopifyStoreModel


class UserModel(Base):
    """
    SQLAlchemy model for users table.
    
    Uses SQLAlchemy 2.0 style with Mapped[T] type hints.
    """
    
    __tablename__ = "users"
    
    # ============================================================
    # Columns (SQLAlchemy 2.0 style)
    # ============================================================
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
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
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # ============================================================
    # Relationships (SQLAlchemy 2.0 style)
    # ============================================================
    subscription: Mapped[Optional["SubscriptionModel"]] = relationship(
        "SubscriptionModel",
        back_populates="user",
        uselist=False,  # One-to-one
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    designs: Mapped[list["DesignModel"]] = relationship(
        "DesignModel",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    orders: Mapped[list["OrderModel"]] = relationship(
        "OrderModel",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    shopify_store: Mapped[Optional["ShopifyStoreModel"]] = relationship(
        "ShopifyStoreModel",
        back_populates="user",
        uselist=False,  # One-to-one
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, email={self.email}, is_active={self.is_active})>"
