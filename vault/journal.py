"""Journal manager for daily markdown files.

This module handles:
- Creating and managing daily journal entries as .md files
- Adding multimodal content blocks (text, images, tables, links)
- Converting journal entries to embeddings
- Syncing with the database
"""

import os
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import List
from uuid import UUID

from .config import get_config
from .models import (
    ContentBlock,
    ImageBlock,
    JournalEntry,
    LinkBlock,
    Memory,
    TableBlock,
    TextBlock,
)


class JournalManager:
    """Manages daily journal entries as markdown files."""

    def __init__(self, vault_db=None):
        """
        Initialize journal manager.

        Args:
            vault_db: Optional VaultDB instance for database operations
        """
        self.config = get_config()
        self.journals_dir = self.config.journals_path
        self.assets_dir = self.journals_dir / "assets"
        self._ensure_directories()
        self._db = vault_db
        self._entries_cache: dict[date, JournalEntry] = {}

    def _ensure_directories(self):
        """Ensure journal directories exist."""
        self.journals_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    @property
    def db(self):
        """Lazy load database connection."""
        if self._db is None:
            from .db import VaultDB
            self._db = VaultDB()
        return self._db

    # ========== Journal Entry Operations ==========

    def get_today(self) -> JournalEntry:
        """Get or create today's journal entry."""
        return self.get_entry(date.today())

    def get_entry(self, entry_date: date) -> JournalEntry:
        """
        Get or create a journal entry for a specific date.

        Args:
            entry_date: The date for the journal entry

        Returns:
            JournalEntry object
        """
        # Check cache first
        if entry_date in self._entries_cache:
            return self._entries_cache[entry_date]

        # Check for existing file
        file_path = self._get_file_path(entry_date)
        if file_path.exists():
            entry = self._load_entry(file_path, entry_date)
        else:
            entry = JournalEntry(date=entry_date, file_path=file_path)

        self._entries_cache[entry_date] = entry
        return entry

    def _get_file_path(self, entry_date: date) -> Path:
        """Get file path for a date's journal entry."""
        # Organize by year/month: journals/2026/03/2026-03-03.md
        year_dir = self.journals_dir / str(entry_date.year)
        month_dir = year_dir / f"{entry_date.month:02d}"
        month_dir.mkdir(parents=True, exist_ok=True)
        return month_dir / f"{entry_date.strftime('%Y-%m-%d')}.md"

    def _load_entry(self, file_path: Path, entry_date: date) -> JournalEntry:
        """Load a journal entry from a markdown file."""
        # For now, create a new entry - full parsing can be added later
        # The .md file is the source of truth for display, but we track metadata
        return JournalEntry(date=entry_date, file_path=file_path)

    # ========== Content Block Operations ==========

    def add_text(
        self,
        content: str,
        entry_date: date | None = None,
        format: str = "markdown",
        language: str | None = None,
    ) -> JournalEntry:
        """
        Add a text block to a journal entry.

        Args:
            content: Text content
            entry_date: Date for the entry (default: today)
            format: Text format (plain, markdown, code)
            language: Programming language for code blocks

        Returns:
            Updated JournalEntry
        """
        entry = self.get_entry(entry_date or date.today())
        block = TextBlock(content=content, format=format, language=language)
        entry.blocks.append(block)
        entry.updated_at = datetime.utcnow()
        self._save_entry(entry)
        return entry

    def add_image(
        self,
        image_path: str,
        entry_date: date | None = None,
        alt_text: str | None = None,
        caption: str | None = None,
        copy_to_vault: bool = True,
    ) -> JournalEntry:
        """
        Add an image block to a journal entry.

        Args:
            image_path: Path to the image file
            entry_date: Date for the entry (default: today)
            alt_text: Alt text for accessibility
            caption: Image caption
            copy_to_vault: Whether to copy image to vault assets

        Returns:
            Updated JournalEntry
        """
        entry = self.get_entry(entry_date or date.today())

        # Copy image to assets folder if requested
        if copy_to_vault:
            src_path = Path(image_path)
            if src_path.exists():
                dest_name = f"{entry.date.strftime('%Y%m%d')}_{src_path.name}"
                dest_path = self.assets_dir / dest_name
                shutil.copy2(src_path, dest_path)
                # Use relative path from journal file to assets
                image_path = f"../assets/{dest_name}"

        block = ImageBlock(path=image_path, alt_text=alt_text, caption=caption)
        entry.blocks.append(block)
        entry.updated_at = datetime.utcnow()
        self._save_entry(entry)
        return entry

    def add_table(
        self,
        headers: List[str],
        rows: List[List[str]],
        entry_date: date | None = None,
        caption: str | None = None,
    ) -> JournalEntry:
        """
        Add a table block to a journal entry.

        Args:
            headers: Table column headers
            rows: Table data rows
            entry_date: Date for the entry (default: today)
            caption: Table caption

        Returns:
            Updated JournalEntry
        """
        entry = self.get_entry(entry_date or date.today())
        block = TableBlock(headers=headers, rows=rows, caption=caption)
        entry.blocks.append(block)
        entry.updated_at = datetime.utcnow()
        self._save_entry(entry)
        return entry

    def add_link(
        self,
        url: str,
        entry_date: date | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> JournalEntry:
        """
        Add a link block to a journal entry.

        Args:
            url: URL to link
            entry_date: Date for the entry (default: today)
            title: Link title
            description: Link description

        Returns:
            Updated JournalEntry
        """
        entry = self.get_entry(entry_date or date.today())
        block = LinkBlock(url=url, title=title, description=description)
        entry.blocks.append(block)
        entry.updated_at = datetime.utcnow()
        self._save_entry(entry)
        return entry

    def add_block(
        self, block: ContentBlock, entry_date: date | None = None
    ) -> JournalEntry:
        """
        Add a content block to a journal entry.

        Args:
            block: ContentBlock to add
            entry_date: Date for the entry (default: today)

        Returns:
            Updated JournalEntry
        """
        entry = self.get_entry(entry_date or date.today())
        entry.blocks.append(block)
        entry.updated_at = datetime.utcnow()
        self._save_entry(entry)
        return entry

    # ========== File Operations ==========

    def _save_entry(self, entry: JournalEntry):
        """Save a journal entry to its markdown file."""
        if entry.file_path is None:
            entry.file_path = self._get_file_path(entry.date)

        # Ensure parent directory exists
        entry.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write markdown content
        markdown_content = entry.to_markdown()
        entry.file_path.write_text(markdown_content, encoding="utf-8")

        # Update cache
        self._entries_cache[entry.date] = entry

    def save_and_sync(self, entry_date: date | None = None) -> Memory:
        """
        Save journal entry and sync to database with embeddings.

        Args:
            entry_date: Date for the entry (default: today)

        Returns:
            Created Memory object
        """
        entry = self.get_entry(entry_date or date.today())
        self._save_entry(entry)

        # Extract text for embedding
        text_content = entry.get_text_for_embedding()

        # Create memory in database
        memory = self.db.add_memory(
            content=text_content,
            type="thought",
            source="journal",
            tags=entry.tags,
            auto_embed=True,
        )

        entry.is_synced = True
        return memory

    # ========== Query Operations ==========

    def list_entries(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> List[JournalEntry]:
        """
        List journal entries in a date range.

        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: today)

        Returns:
            List of JournalEntry objects
        """
        from datetime import timedelta

        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=30))

        entries = []
        current = start_date
        while current <= end_date:
            file_path = self._get_file_path(current)
            if file_path.exists():
                entries.append(self.get_entry(current))
            current += timedelta(days=1)

        return entries

    def get_entry_markdown(self, entry_date: date | None = None) -> str:
        """
        Get the markdown content of a journal entry.

        Args:
            entry_date: Date for the entry (default: today)

        Returns:
            Markdown string
        """
        entry = self.get_entry(entry_date or date.today())
        return entry.to_markdown()

    def read_entry_file(self, entry_date: date | None = None) -> str | None:
        """
        Read the raw content of a journal markdown file.

        Args:
            entry_date: Date for the entry (default: today)

        Returns:
            File content or None if file doesn't exist
        """
        file_path = self._get_file_path(entry_date or date.today())
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return None


# Convenience functions for direct use


def today() -> JournalEntry:
    """Get today's journal entry."""
    return JournalManager().get_today()


def add_text(content: str, **kwargs) -> JournalEntry:
    """Add text to today's journal."""
    return JournalManager().add_text(content, **kwargs)


def add_image(image_path: str, **kwargs) -> JournalEntry:
    """Add an image to today's journal."""
    return JournalManager().add_image(image_path, **kwargs)


def add_table(headers: List[str], rows: List[List[str]], **kwargs) -> JournalEntry:
    """Add a table to today's journal."""
    return JournalManager().add_table(headers, rows, **kwargs)


def add_link(url: str, **kwargs) -> JournalEntry:
    """Add a link to today's journal."""
    return JournalManager().add_link(url, **kwargs)
