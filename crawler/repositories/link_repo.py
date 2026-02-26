"""Discovered link repository for database operations."""

from typing import Optional, List
from datetime import datetime

from crawler.models.parsed_result import DiscoveredLink, RelationshipType
from crawler.db.connection import DatabaseConnection


class LinkRepository:
    """Repository for discovered link database operations."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def add(self, link: DiscoveredLink) -> int:
        """Add a discovered link. Returns the link ID."""
        cursor = await self.db.execute(
            """
            INSERT INTO discovered_links (
                source_task_id, url, relationship_type, priority_delta
            ) VALUES (?, ?, ?, ?)
            """,
            (
                link.source_task_id,
                link.url,
                link.relationship_type.value,
                link.priority_delta,
            ),
        )
        await self.db.commit()
        return cursor.lastrowid

    async def add_batch(self, links: List[DiscoveredLink]) -> int:
        """Add multiple links. Returns count of added links."""
        if not links:
            return 0

        await self.db.executemany(
            """
            INSERT INTO discovered_links (
                source_task_id, url, relationship_type, priority_delta
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (
                    link.source_task_id,
                    link.url,
                    link.relationship_type.value,
                    link.priority_delta,
                )
                for link in links
            ],
        )
        await self.db.commit()
        return len(links)

    async def get_unprocessed(self, source_task_id: Optional[str] = None) -> List[DiscoveredLink]:
        """Get unprocessed links."""
        if source_task_id:
            rows = await self.db.fetchall(
                """
                SELECT * FROM discovered_links 
                WHERE source_task_id = ? AND processed = FALSE
                ORDER BY priority_delta DESC, added_at ASC
                """,
                (source_task_id,),
            )
        else:
            rows = await self.db.fetchall(
                """
                SELECT * FROM discovered_links 
                WHERE processed = FALSE
                ORDER BY priority_delta DESC, added_at ASC
                """,
            )

        return [self._row_to_link(row) for row in rows]

    async def mark_processed(self, link_id: int) -> None:
        """Mark link as processed."""
        await self.db.execute(
            "UPDATE discovered_links SET processed = TRUE WHERE id = ?",
            (link_id,),
        )
        await self.db.commit()

    async def mark_processed_by_url(self, url: str) -> None:
        """Mark link as processed by URL."""
        await self.db.execute(
            "UPDATE discovered_links SET processed = TRUE WHERE url = ?",
            (url,),
        )
        await self.db.commit()

    async def get_by_source(self, source_task_id: str) -> List[DiscoveredLink]:
        """Get all links for a source task."""
        rows = await self.db.fetchall(
            """
            SELECT * FROM discovered_links 
            WHERE source_task_id = ?
            ORDER BY priority_delta DESC, added_at ASC
            """,
            (source_task_id,),
        )
        return [self._row_to_link(row) for row in rows]

    async def count_unprocessed(self) -> int:
        """Count unprocessed links."""
        row = await self.db.fetchone(
            "SELECT COUNT(*) as count FROM discovered_links WHERE processed = FALSE"
        )
        return row["count"] if row else 0

    async def delete(self, link_id: int) -> None:
        """Delete link."""
        await self.db.execute(
            "DELETE FROM discovered_links WHERE id = ?",
            (link_id,),
        )
        await self.db.commit()

    async def delete_by_source(self, source_task_id: str) -> None:
        """Delete all links for a source task."""
        await self.db.execute(
            "DELETE FROM discovered_links WHERE source_task_id = ?",
            (source_task_id,),
        )
        await self.db.commit()

    def _row_to_link(self, row: aiosqlite.Row) -> DiscoveredLink:
        """Convert database row to DiscoveredLink."""
        return DiscoveredLink(
            url=row["url"],
            relationship_type=RelationshipType(row["relationship_type"]) if row["relationship_type"] else RelationshipType.UNKNOWN,
            priority_delta=row["priority_delta"],
            source_task_id=row["source_task_id"],
        )
