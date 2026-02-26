"""Priority calculator for task scheduling."""

from typing import Dict, Optional
from datetime import datetime, timedelta


class PriorityCalculator:
    """
    Calculates task priorities based on various factors.
    
    Priority factors:
    - Base priority from config
    - Relationship type (owner, county, parcel, etc.)
    - Age of task
    - Retry count
    - Custom boost rules
    """

    # Default priority deltas by relationship type
    RELATIONSHIP_DELTAS = {
        "owner": 5,
        "county": 3,
        "parcel": 2,
        "neighbor": 1,
        "related": 0,
        "unknown": 0,
    }

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.base_priority = self.config.get("base_priority", 0)
        self.relationship_deltas = {
            **self.RELATIONSHIP_DELTAS,
            **self.config.get("relationship_deltas", {}),
        }

    def calculate(
        self,
        relationship_type: Optional[str] = None,
        created_at: Optional[datetime] = None,
        retry_count: int = 0,
        custom_boost: int = 0,
    ) -> int:
        """
        Calculate task priority.
        
        Args:
            relationship_type: Type of relationship (owner, county, etc.)
            created_at: Task creation time
            retry_count: Number of retries
            custom_boost: Custom priority boost
        
        Returns:
            Priority value (higher = more urgent)
        """
        priority = self.base_priority

        # Add relationship delta
        if relationship_type:
            delta = self.relationship_deltas.get(relationship_type.lower(), 0)
            priority += delta

        # Add age boost (older tasks get higher priority)
        if created_at:
            age_boost = self._calculate_age_boost(created_at)
            priority += age_boost

        # Add retry boost (failed tasks get higher priority)
        if retry_count > 0:
            priority += retry_count * 2

        # Add custom boost
        priority += custom_boost

        return priority

    def _calculate_age_boost(self, created_at: datetime) -> int:
        """Calculate priority boost based on task age."""
        now = datetime.utcnow()
        age = now - created_at

        # Boost by 1 for every hour old
        hours_old = age.total_seconds() / 3600
        return min(int(hours_old), 10)  # Cap at 10

    def boost_priority(
        self,
        current_priority: int,
        factor: float = 1.5,
        max_boost: int = 20,
    ) -> int:
        """
        Apply priority boost.
        
        Args:
            current_priority: Current priority value
            factor: Multiplication factor
            max_boost: Maximum boost to apply
        
        Returns:
            New priority value
        """
        boost = int(current_priority * (factor - 1))
        boost = min(boost, max_boost)
        return current_priority + boost

    def decay_priority(
        self,
        current_priority: int,
        factor: float = 0.9,
        min_priority: int = 0,
    ) -> int:
        """
        Apply priority decay.
        
        Args:
            current_priority: Current priority value
            factor: Decay factor
            min_priority: Minimum priority value
        
        Returns:
            New priority value
        """
        new_priority = int(current_priority * factor)
        return max(new_priority, min_priority)
