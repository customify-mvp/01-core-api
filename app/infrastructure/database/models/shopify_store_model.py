"""
ShopifyStoreModel - SQLAlchemy model for shopify_stores table.

Represents Shopify store integrations with OAuth tokens.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.session import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.user_model import UserModel


class ShopifyStoreModel(Base):
    """
    SQLAlchemy model for shopify_stores table.
    
    Stores Shopify OAuth credentials and integration status.
    Uses SQLAlchemy 2.0 style with Mapped[T] type hints.
    """
    
    __tablename__ = "shopify_stores"
    
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
    shop_domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    uninstalled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # ============================================================
    # Relationships (SQLAlchemy 2.0 style)
    # ============================================================
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="shopify_store",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<ShopifyStoreModel(id={self.id}, user_id={self.user_id}, shop_domain={self.shop_domain}, is_active={self.is_active})>"
