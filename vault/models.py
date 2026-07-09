"""Pydantic models for Vault data structures."""

import json
from datetime import datetime, date as date_type
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ========== Content Block Types (Multimodal Support) ==========


class TextBlock(BaseModel):
    """Text content block."""
    
    block_type: Literal["text"] = "text"
    content: str
    format: Literal["plain", "markdown", "code"] = "markdown"
    language: str | None = None  # For code blocks


class ImageBlock(BaseModel):
    """Image content block."""
    
    block_type: Literal["image"] = "image"
    path: str  # Local path or URL
    alt_text: str | None = None
    caption: str | None = None
    width: int | None = None
    height: int | None = None


class TableBlock(BaseModel):
    """Table content block."""
    
    block_type: Literal["table"] = "table"
    headers: list[str]
    rows: list[list[str]]
    caption: str | None = None


class LinkBlock(BaseModel):
    """Link/reference content block."""
    
    block_type: Literal["link"] = "link"
    url: str
    title: str | None = None
    description: str | None = None


ContentBlock = TextBlock | ImageBlock | TableBlock | LinkBlock


# ========== Journal Entry (Daily .md file) ==========


class JournalEntry(BaseModel):
    """A daily journal entry that gets saved as a .md file."""
    
    id: UUID = Field(default_factory=uuid4)
    date: date_type = Field(default_factory=date_type.today)
    title: str | None = None  # Optional title for the day
    blocks: list[ContentBlock] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    project_id: UUID | None = None
    file_path: Path | None = None  # Path to the generated .md file
    is_synced: bool = False  # Whether embeddings are generated
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_markdown(self) -> str:
        """Convert journal entry to markdown format."""
        lines = []
        
        # Header
        date_str = self.date.strftime("%Y-%m-%d")
        title = self.title or f"Journal - {date_str}"
        lines.append(f"# {title}")
        lines.append(f"\n> Date: {date_str}")
        
        if self.tags:
            lines.append(f"> Tags: {', '.join(self.tags)}")
        
        lines.append("")
        
        # Content blocks
        for block in self.blocks:
            lines.append(self._block_to_markdown(block))
            lines.append("")
        
        # Footer metadata
        lines.append("---")
        lines.append(f"*Entry ID: {self.id}*")
        
        return "\n".join(lines)
    
    def _block_to_markdown(self, block: ContentBlock) -> str:
        """Convert a content block to markdown."""
        if isinstance(block, TextBlock):
            if block.format == "code" and block.language:
                return f"```{block.language}\n{block.content}\n```"
            return block.content
        
        elif isinstance(block, ImageBlock):
            alt = block.alt_text or "image"
            md = f"![{alt}]({block.path})"
            if block.caption:
                md += f"\n*{block.caption}*"
            return md
        
        elif isinstance(block, TableBlock):
            lines = []
            if block.caption:
                lines.append(f"**{block.caption}**\n")
            
            # Header
            lines.append("| " + " | ".join(block.headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(block.headers)) + " |")
            
            # Rows
            for row in block.rows:
                lines.append("| " + " | ".join(row) + " |")
            
            return "\n".join(lines)
        
        elif isinstance(block, LinkBlock):
            title = block.title or block.url
            md = f"[{title}]({block.url})"
            if block.description:
                md += f" - {block.description}"
            return md
        
        return ""
    
    def get_text_for_embedding(self) -> str:
        """Extract all text content for embedding generation."""
        texts = []
        
        if self.title:
            texts.append(self.title)
        
        for block in self.blocks:
            if isinstance(block, TextBlock):
                texts.append(block.content)
            elif isinstance(block, ImageBlock):
                if block.alt_text:
                    texts.append(block.alt_text)
                if block.caption:
                    texts.append(block.caption)
            elif isinstance(block, TableBlock):
                if block.caption:
                    texts.append(block.caption)
                texts.append(" ".join(block.headers))
                for row in block.rows:
                    texts.append(" ".join(row))
            elif isinstance(block, LinkBlock):
                if block.title:
                    texts.append(block.title)
                if block.description:
                    texts.append(block.description)
        
        return "\n\n".join(texts)


# ========== Project Model ==========


class Project(BaseModel):
    """Project model."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    status: Literal["active", "paused", "completed", "archived"] = "active"
    description: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ========== Memory Model (Enhanced for Multimodal) ==========


class Memory(BaseModel):
    """Memory model (core data unit) - now supports multimodal content."""

    id: UUID = Field(default_factory=uuid4)
    content: str  # Text content or extracted text from multimodal
    content_type: Literal["text", "image", "table", "link", "journal"] = "text"
    type: Literal[
        "thought", "idea", "progress", "decision", "question", "workflow", "reference"
    ] = "thought"
    source: Literal["cli", "api", "file", "voice", "web", "journal", "mcp"] = "cli"
    project_id: UUID | None = None
    journal_entry_id: UUID | None = None  # Link to parent journal entry
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)  # Store media URLs, dimensions, etc.
    file_path: str | None = None  # Path to associated .md file
    doc_path: str | None = None  # Relative path inside vault_store/ for linked documents
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Embedding(BaseModel):
    """Embedding model (vector representation)."""

    id: UUID = Field(default_factory=uuid4)
    memory_id: UUID
    vector: list[float]
    model_name: str
    model_version: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("vector", mode="before")
    @classmethod
    def parse_vector(cls, value):
        """Accept pgvector values returned as JSON-like strings."""
        if isinstance(value, str):
            value = json.loads(value)
        return value


class MemoryLink(BaseModel):
    """Memory relationship model."""

    id: UUID = Field(default_factory=uuid4)
    from_memory_id: UUID
    to_memory_id: UUID
    relation_type: Literal["related", "references", "contradicts", "extends"]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchResult(BaseModel):
    """Search result with similarity score."""

    memory: Memory
    similarity: float
    embedding_model: str
