"""
Design repository interface (Domain layer).

Defines contract for design persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from app.domain.entities.design import Design, DesignStatus


class IDesignRepository(ABC):
    """
    Design repository interface.
    
    Handles design CRUD and query operations.
    """
    
    @abstractmethod
    async def create(self, design: Design) -> Design:
        """
        Create new design.
        
        Args:
            design: Design entity to persist
            
        Returns:
            Created design entity
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, design_id: str) -> Optional[Design]:
        """
        Get design by ID.
        
        Args:
            design_id: Design unique identifier
            
        Returns:
            Design entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_user(
        self, 
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[DesignStatus] = None
    ) -> Tuple[List[Design], int]:
        """
        Get user's designs with pagination and count.
        
        Args:
            user_id: User unique identifier
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            status: Filter by design status (optional)
            
        Returns:
            Tuple of (list of designs, total count)
        """
        pass
    
    @abstractmethod
    async def update(self, design: Design) -> Design:
        """
        Update existing design.
        
        Args:
            design: Design entity with updated fields
            
        Returns:
            Updated design entity
            
        Raises:
            Exception: If design not found
        """
        pass
    
    @abstractmethod
    async def delete(self, design_id: str) -> bool:
        """
        Soft delete design (sets is_deleted=True).
        
        Args:
            design_id: Design unique identifier
            
        Returns:
            True if design was deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count_by_user(
        self, 
        user_id: str,
        status: Optional[DesignStatus] = None
    ) -> int:
        """
        Count user's designs.
        
        Useful for subscription quota validation.
        
        Args:
            user_id: User unique identifier
            status: Filter by design status (optional)
            
        Returns:
            Number of designs
        """
        pass
