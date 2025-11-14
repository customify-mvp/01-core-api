"""
OrderModel - SQLAlchemy model for orders table.

Represents orders placed through integrations (Shopify, WooCommerce).
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.session import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.user_model import UserModel
    from app.infrastructure.database.models.design_model import DesignModel


class OrderModel(Base):
    """
    SQLAlchemy model for orders table.
    
    Tracks orders from external platforms with PDF generation status.
    Uses SQLAlchemy 2.0 style with Mapped[T] type hints.
    """
    
    __tablename__ = "orders"
    
    # ============================================================
    # Columns (SQLAlchemy 2.0 style)
    # ============================================================
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    design_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("designs.id", ondelete="SET NULL")
    )
    external_order_id: Mapped[Optional[str]] = mapped_column(String(255))
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="pending"
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # ============================================================
    # Relationships (SQLAlchemy 2.0 style)
    # ============================================================
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="orders",
        lazy="selectin"
    )
    
    design: Mapped[Optional["DesignModel"]] = relationship(
        "DesignModel",
        back_populates="orders",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<OrderModel(id={self.id}, user_id={self.user_id}, platform={self.platform}, status={self.status})>"
