"""
Order domain entity (pure business logic).

NO framework dependencies - pure Python only.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class OrderStatus(Enum):
    """Order status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderPlatform(Enum):
    """Order platform sources."""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MANUAL = "manual"


@dataclass
class Order:
    """
    Order domain entity representing an order from an external platform.
    
    This is pure business logic with NO external dependencies.
    NO SQLAlchemy, NO Pydantic, NO FastAPI.
    """
    
    id: str
    user_id: str
    design_id: Optional[str]
    external_order_id: Optional[str]
    platform: OrderPlatform
    pdf_url: Optional[str]
    status: OrderStatus
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    
    @staticmethod
    def create(
        user_id: str,
        platform: OrderPlatform,
        design_id: Optional[str] = None,
        external_order_id: Optional[str] = None
    ) -> "Order":
        """
        Factory method to create a new order.
        
        Args:
            user_id: User ID who owns this order
            platform: Platform where order originated (shopify, woocommerce, manual)
            design_id: Design ID to use for this order (optional)
            external_order_id: Order ID from external platform (optional)
            
        Returns:
            New Order instance with PENDING status
        """
        from uuid import uuid4
        
        return Order(
            id=str(uuid4()),
            user_id=user_id,
            design_id=design_id,
            external_order_id=external_order_id,
            platform=platform,
            pdf_url=None,
            status=OrderStatus.PENDING,
            error_message=None,
            created_at=datetime.utcnow(),
            processed_at=None
        )
    
    def mark_processing(self) -> None:
        """
        Mark order as being processed.
        
        Raises:
            ValueError: If order is not in PENDING status
        """
        if self.status != OrderStatus.PENDING:
            raise ValueError(
                f"Can only process PENDING orders. Current status: {self.status.value}"
            )
        
        self.status = OrderStatus.PROCESSING
    
    def mark_completed(self, pdf_url: str) -> None:
        """
        Mark order as completed with generated PDF.
        
        Args:
            pdf_url: URL to generated PDF file
            
        Raises:
            ValueError: If order is not PROCESSING or pdf_url is empty
        """
        if self.status != OrderStatus.PROCESSING:
            raise ValueError(
                f"Can only complete PROCESSING orders. Current status: {self.status.value}"
            )
        
        if not pdf_url or not pdf_url.strip():
            raise ValueError("pdf_url cannot be empty")
        
        self.status = OrderStatus.COMPLETED
        self.pdf_url = pdf_url
        self.processed_at = datetime.utcnow()
        self.error_message = None  # Clear any previous errors
    
    def mark_failed(self, error_message: str) -> None:
        """
        Mark order as failed with error message.
        
        Args:
            error_message: Error message describing the failure
            
        Raises:
            ValueError: If order is not PROCESSING or error_message is empty
        """
        if self.status != OrderStatus.PROCESSING:
            raise ValueError(
                f"Can only fail PROCESSING orders. Current status: {self.status.value}"
            )
        
        if not error_message or not error_message.strip():
            raise ValueError("error_message cannot be empty")
        
        self.status = OrderStatus.FAILED
        self.error_message = error_message
        self.processed_at = datetime.utcnow()
    
    def retry(self) -> None:
        """
        Retry a failed order.
        
        Resets status to PENDING and clears error_message.
        
        Raises:
            ValueError: If order is not in FAILED status
        """
        if self.status != OrderStatus.FAILED:
            raise ValueError(
                f"Can only retry FAILED orders. Current status: {self.status.value}"
            )
        
        self.status = OrderStatus.PENDING
        self.error_message = None
        self.pdf_url = None
        self.processed_at = None
    
    def is_completed(self) -> bool:
        """
        Check if order is completed.
        
        Returns:
            True if order is completed
        """
        return self.status == OrderStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """
        Check if order failed.
        
        Returns:
            True if order failed
        """
        return self.status == OrderStatus.FAILED
    
    def can_be_retried(self) -> bool:
        """
        Check if order can be retried.
        
        Returns:
            True if order is in FAILED status
        """
        return self.status == OrderStatus.FAILED
