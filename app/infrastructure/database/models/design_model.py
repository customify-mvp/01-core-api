"""
DesignModel - SQLAlchemy model for designs table.

Represents user-created designs for products.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.infrastructure.database.session import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.user_model import UserModel
    from app.infrastructure.database.models.order_model import OrderModel


class DesignModel(Base):
    """
    SQLAlchemy model for designs table.
    
    Stores user-created designs with JSONB data and rendering status.
    Uses SQLAlchemy 2.0 style with Mapped[T] type hints.
    """
    
    __tablename__ = "designs"
    
    # ============================================================
    # Columns (SQLAlchemy 2.0 style)
    # ============================================================
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    design_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="draft"
    )
    preview_url: Mapped[Optional[str]] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
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
    
    # ============================================================
    # Relationships (SQLAlchemy 2.0 style)
    # ============================================================
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="designs",
        lazy="selectin"
    )
    
    orders: Mapped[list["OrderModel"]] = relationship(
        "OrderModel",
        back_populates="design",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<DesignModel(id={self.id}, user_id={self.user_id}, product_type={self.product_type}, status={self.status})>"
