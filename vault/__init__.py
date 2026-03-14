"""Vault - AI-native Second Brain with multimodal journals and MCP support."""

__version__ = "0.2.0"

from .models import (
    Memory,
    Project,
    JournalEntry,
    TextBlock,
    ImageBlock,
    TableBlock,
    LinkBlock,
)
from .journal import JournalManager, add_text, add_image, add_table, add_link, today
from .db import VaultDB
from .config import get_config

__all__ = [
    "VaultDB",
    "JournalManager",
    "Memory",
    "Project",
    "JournalEntry",
    "TextBlock",
    "ImageBlock",
    "TableBlock",
    "LinkBlock",
    "add_text",
    "add_image",
    "add_table",
    "add_link",
    "today",
    "get_config",
]
