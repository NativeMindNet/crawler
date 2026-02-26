"""Database connection manager."""

import aiosqlite
from pathlib import Path
from typing import Optional
import asyncio

from crawler.db.schema import SCHEMA_SQL


class DatabaseConnection:
    """Manages SQLite database connections."""

    _instance: Optional["DatabaseConnection"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    @classmethod
    async def get_instance(cls, db_path: str) -> "DatabaseConnection":
        """Get singleton instance."""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
                    await cls._instance.connect()
        return cls._instance

    async def connect(self) -> None:
        """Connect to database and initialize schema."""
        # Ensure directory exists
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row

        # Enable WAL mode for better concurrency
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA synchronous=NORMAL")

        # Initialize schema
        await self._db.executescript(SCHEMA_SQL)
        await self._db.commit()

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def connection(self) -> aiosqlite.Connection:
        """Get database connection."""
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db

    async def execute(self, query: str, parameters: tuple = None) -> aiosqlite.Cursor:
        """Execute a query."""
        if parameters:
            return await self._db.execute(query, parameters)
        return await self._db.execute(query)

    async def executemany(self, query: str, parameters: list) -> aiosqlite.Cursor:
        """Execute many queries."""
        return await self._db.executemany(query, parameters)

    async def fetchone(self, query: str, parameters: tuple = None) -> Optional[aiosqlite.Row]:
        """Fetch one row."""
        if parameters:
            async with self._db.execute(query, parameters) as cursor:
                return await cursor.fetchone()
        async with self._db.execute(query) as cursor:
            return await cursor.fetchone()

    async def fetchall(self, query: str, parameters: tuple = None) -> list:
        """Fetch all rows."""
        if parameters:
            async with self._db.execute(query, parameters) as cursor:
                return await cursor.fetchall()
        async with self._db.execute(query) as cursor:
            return await cursor.fetchall()

    async def commit(self) -> None:
        """Commit transaction."""
        await self._db.commit()

    async def close(self) -> None:
        """Close connection."""
        await self.disconnect()


# Global connection instance
_db_connection: Optional[DatabaseConnection] = None


async def get_connection(db_path: str) -> DatabaseConnection:
    """Get database connection."""
    return await DatabaseConnection.get_instance(db_path)


async def init_database(db_path: str) -> DatabaseConnection:
    """Initialize database."""
    conn = await get_connection(db_path)
    return conn
