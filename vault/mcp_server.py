"""MCP (Model Context Protocol) Server for Vault.

This module implements an MCP server that allows any compatible IDE
(VS Code, Claude Code, Windsurf, Cursor, etc.) to interact with the vault.

Features exposed via MCP:
- Add memories (text, images, tables, links)
- Search memories semantically
- Manage journal entries
- Query recent memories
- Project management
"""

import asyncio
import json
from datetime import date, datetime
from typing import Any, Sequence
from uuid import UUID

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    ResourceContents,
    TextContent,
    Tool,
)
from pydantic import AnyUrl


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("vault-mcp")

    # Lazy imports to avoid circular dependencies
    _db = None
    _journal = None

    def get_db():
        nonlocal _db
        if _db is None:
            from .db import VaultDB
            _db = VaultDB()
        return _db

    def get_journal():
        nonlocal _journal
        if _journal is None:
            from .journal import JournalManager
            _journal = JournalManager()
        return _journal

    # ========== Tools ==========

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available vault tools."""
        return [
            Tool(
                name="vault_add_text",
                description="Add a text memory or journal entry to the vault. Supports markdown formatting.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The text content to add",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["thought", "idea", "progress", "decision", "question", "workflow", "reference"],
                            "description": "Type of memory",
                            "default": "thought",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorization",
                        },
                        "to_journal": {
                            "type": "boolean",
                            "description": "Add to today's journal instead of direct memory",
                            "default": False,
                        },
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="vault_add_table",
                description="Add a table to today's journal entry",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "headers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Table column headers",
                        },
                        "rows": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "description": "Table rows (2D array)",
                        },
                        "caption": {
                            "type": "string",
                            "description": "Optional table caption",
                        },
                    },
                    "required": ["headers", "rows"],
                },
            ),
            Tool(
                name="vault_add_link",
                description="Add a link/reference to today's journal entry",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to add",
                        },
                        "title": {
                            "type": "string",
                            "description": "Link title",
                        },
                        "description": {
                            "type": "string",
                            "description": "Link description",
                        },
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="vault_add_image",
                description="Add an image reference to today's journal entry",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the image file",
                        },
                        "alt_text": {
                            "type": "string",
                            "description": "Alt text for accessibility",
                        },
                        "caption": {
                            "type": "string",
                            "description": "Image caption",
                        },
                    },
                    "required": ["image_path"],
                },
            ),
            Tool(
                name="vault_search",
                description="Semantically search memories in the vault by meaning",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results to return",
                            "default": 10,
                        },
                        "type": {
                            "type": "string",
                            "enum": ["thought", "idea", "progress", "decision", "question", "workflow", "reference"],
                            "description": "Filter by memory type",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="vault_recent",
                description="Get recent memories from the vault",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results to return",
                            "default": 10,
                        },
                        "type": {
                            "type": "string",
                            "enum": ["thought", "idea", "progress", "decision", "question", "workflow", "reference"],
                            "description": "Filter by memory type",
                        },
                    },
                },
            ),
            Tool(
                name="vault_journal_today",
                description="Get today's journal entry content",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="vault_journal_sync",
                description="Save and sync today's journal to the database with embeddings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (default: today)",
                        },
                    },
                },
            ),
            Tool(
                name="vault_project_list",
                description="List all projects in the vault",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["active", "paused", "completed", "archived"],
                            "description": "Filter by project status",
                        },
                    },
                },
            ),
            Tool(
                name="vault_project_create",
                description="Create a new project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Project name",
                        },
                        "description": {
                            "type": "string",
                            "description": "Project description",
                        },
                    },
                    "required": ["name"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
        """Handle tool calls."""
        arguments = arguments or {}

        try:
            if name == "vault_add_text":
                content = arguments["content"]
                memory_type = arguments.get("type", "thought")
                tags = arguments.get("tags", [])
                to_journal = arguments.get("to_journal", False)

                if to_journal:
                    journal = get_journal()
                    entry = journal.add_text(content)
                    return [TextContent(
                        type="text",
                        text=f"Added to today's journal ({entry.date}). Entry now has {len(entry.blocks)} block(s).",
                    )]
                else:
                    db = get_db()
                    memory = db.add_memory(
                        content=content,
                        type=memory_type,
                        source="mcp",
                        tags=tags,
                    )
                    return [TextContent(
                        type="text",
                        text=f"Memory added successfully. ID: {memory.id}",
                    )]

            elif name == "vault_add_table":
                journal = get_journal()
                headers = arguments["headers"]
                rows = arguments["rows"]
                caption = arguments.get("caption")
                entry = journal.add_table(headers, rows, caption=caption)
                return [TextContent(
                    type="text",
                    text=f"Table added to today's journal ({entry.date}). {len(headers)} columns, {len(rows)} rows.",
                )]

            elif name == "vault_add_link":
                journal = get_journal()
                entry = journal.add_link(
                    url=arguments["url"],
                    title=arguments.get("title"),
                    description=arguments.get("description"),
                )
                return [TextContent(
                    type="text",
                    text=f"Link added to today's journal ({entry.date}).",
                )]

            elif name == "vault_add_image":
                journal = get_journal()
                entry = journal.add_image(
                    image_path=arguments["image_path"],
                    alt_text=arguments.get("alt_text"),
                    caption=arguments.get("caption"),
                )
                return [TextContent(
                    type="text",
                    text=f"Image added to today's journal ({entry.date}).",
                )]

            elif name == "vault_search":
                db = get_db()
                query = arguments["query"]
                limit = arguments.get("limit", 10)
                memory_type = arguments.get("type")

                results = db.search_memories(query, limit=limit)

                if not results:
                    return [TextContent(type="text", text="No matching memories found.")]

                output_lines = [f"Found {len(results)} matching memories:\n"]
                for i, result in enumerate(results, 1):
                    memory = result.memory
                    similarity = result.similarity
                    output_lines.append(
                        f"{i}. [{memory.type}] (similarity: {similarity:.3f})\n"
                        f"   {memory.content[:200]}{'...' if len(memory.content) > 200 else ''}\n"
                        f"   Tags: {', '.join(memory.tags) if memory.tags else 'none'}\n"
                    )

                return [TextContent(type="text", text="\n".join(output_lines))]

            elif name == "vault_recent":
                db = get_db()
                limit = arguments.get("limit", 10)
                memory_type = arguments.get("type")

                memories = db.recent_memories(limit=limit, type=memory_type)

                if not memories:
                    return [TextContent(type="text", text="No recent memories found.")]

                output_lines = [f"Recent {len(memories)} memories:\n"]
                for i, memory in enumerate(memories, 1):
                    output_lines.append(
                        f"{i}. [{memory.type}] {memory.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                        f"   {memory.content[:200]}{'...' if len(memory.content) > 200 else ''}\n"
                    )

                return [TextContent(type="text", text="\n".join(output_lines))]

            elif name == "vault_journal_today":
                journal = get_journal()
                markdown = journal.get_entry_markdown()
                return [TextContent(type="text", text=markdown)]

            elif name == "vault_journal_sync":
                journal = get_journal()
                date_str = arguments.get("date")
                entry_date = None
                if date_str:
                    entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                memory = journal.save_and_sync(entry_date)
                return [TextContent(
                    type="text",
                    text=f"Journal synced successfully. Memory ID: {memory.id}",
                )]

            elif name == "vault_project_list":
                db = get_db()
                status = arguments.get("status")
                projects = db.list_projects(status=status)

                if not projects:
                    return [TextContent(type="text", text="No projects found.")]

                output_lines = [f"Found {len(projects)} projects:\n"]
                for project in projects:
                    output_lines.append(
                        f"- {project.name} [{project.status}]\n"
                        f"  {project.description or 'No description'}\n"
                    )

                return [TextContent(type="text", text="\n".join(output_lines))]

            elif name == "vault_project_create":
                db = get_db()
                project = db.create_project(
                    name=arguments["name"],
                    description=arguments.get("description"),
                )
                return [TextContent(
                    type="text",
                    text=f"Project '{project.name}' created. ID: {project.id}",
                )]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # ========== Resources ==========

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available vault resources."""
        journal = get_journal()

        resources = [
            Resource(
                uri=AnyUrl("vault://journal/today"),
                name="Today's Journal",
                description="Current day's journal entry",
                mimeType="text/markdown",
            ),
        ]

        # Add recent journal entries as resources
        entries = journal.list_entries()
        for entry in entries[:7]:  # Last 7 days
            resources.append(
                Resource(
                    uri=AnyUrl(f"vault://journal/{entry.date.isoformat()}"),
                    name=f"Journal {entry.date.isoformat()}",
                    description=f"Journal entry for {entry.date.strftime('%B %d, %Y')}",
                    mimeType="text/markdown",
                )
            )

        return resources

    @server.read_resource()
    async def read_resource(uri: AnyUrl) -> str:
        """Read a vault resource."""
        uri_str = str(uri)

        if uri_str.startswith("vault://journal/"):
            journal = get_journal()
            date_part = uri_str.replace("vault://journal/", "")

            if date_part == "today":
                return journal.get_entry_markdown()
            else:
                entry_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                content = journal.read_entry_file(entry_date)
                return content or f"No journal entry for {date_part}"

        return f"Unknown resource: {uri}"

    return server


async def main():
    """Run the MCP server."""
    server = create_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="vault-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={},
                ),
            ),
        )


def run_server():
    """Entry point for running the MCP server."""
    asyncio.run(main())


if __name__ == "__main__":
    run_server()
