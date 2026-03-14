"""CLI interface for Vault - Your Second Brain."""

from typing import Optional
from uuid import UUID

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from .config import get_config, reload_config
from .db import VaultDB

app = typer.Typer(
    name="vault",
    help="🧠 Vault - Your AI-native Second Brain",
    add_completion=False,
)
console = Console()


# ========== Memory Commands ==========


@app.command()
def add(
    content: str = typer.Argument(..., help="Memory content"),
    type: str = typer.Option("thought", help="Memory type"),
    project: Optional[str] = typer.Option(None, help="Project name"),
    tags: Optional[str] = typer.Option(None, help="Comma-separated tags"),
):
    """Add a new memory to your vault."""
    db = VaultDB()

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    # TODO: Handle project name -> ID lookup
    project_id = UUID(project) if project else None

    memory = db.add_memory(
        content=content, type=type, project_id=project_id, tags=tag_list
    )

    rprint(f"[green]✓[/green] Memory added: {memory.id}")
    rprint(f"  Type: {memory.type}")
    rprint(f"  Tags: {', '.join(memory.tags) if memory.tags else 'none'}")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, help="Maximum results"),
):
    """Search memories by semantic similarity."""
    db = VaultDB()

    rprint(f"[cyan]Searching for:[/cyan] {query}")
    results = db.search_memories(query, limit=limit)

    if not results:
        rprint("[yellow]No results found[/yellow]")
        return

    table = Table(title="Search Results")
    table.add_column("Similarity", style="cyan", width=10)
    table.add_column("Type", style="green", width=10)
    table.add_column("Content", style="white")
    table.add_column("Tags", style="yellow")

    for result in results:
        similarity_pct = f"{result.similarity * 100:.1f}%"
        tags_str = ", ".join(result.memory.tags[:3])  # Show first 3 tags
        content_preview = (
            result.memory.content[:80] + "..."
            if len(result.memory.content) > 80
            else result.memory.content
        )
        table.add_row(similarity_pct, result.memory.type, content_preview, tags_str)

    console.print(table)
    rprint(f"\n[dim]Model: {results[0].embedding_model}[/dim]")


@app.command()
def recent(
    limit: int = typer.Option(10, help="Number of memories to show"),
    type: Optional[str] = typer.Option(None, help="Filter by type"),
):
    """Show recent memories."""
    db = VaultDB()

    memories = db.recent_memories(limit=limit, type=type)

    if not memories:
        rprint("[yellow]No memories found[/yellow]")
        return

    table = Table(title=f"Recent Memories ({len(memories)})")
    table.add_column("Date", style="cyan", width=20)
    table.add_column("Type", style="green", width=10)
    table.add_column("Content", style="white")

    for memory in memories:
        date_str = memory.created_at.strftime("%Y-%m-%d %H:%M")
        content_preview = (
            memory.content[:80] + "..."
            if len(memory.content) > 80
            else memory.content
        )
        table.add_row(date_str, memory.type, content_preview)

    console.print(table)


# ========== Project Commands ==========

project_app = typer.Typer(help="Manage projects")
app.add_typer(project_app, name="project")


@project_app.command("create")
def project_create(
    name: str = typer.Argument(..., help="Project name"),
    description: Optional[str] = typer.Option(None, help="Project description"),
):
    """Create a new project."""
    db = VaultDB()
    project = db.create_project(name=name, description=description)

    rprint(f"[green]✓[/green] Project created: {project.name}")
    rprint(f"  ID: {project.id}")
    rprint(f"  Status: {project.status}")


@project_app.command("list")
def project_list(status: Optional[str] = typer.Option(None, help="Filter by status")):
    """List all projects."""
    db = VaultDB()
    projects = db.list_projects(status=status)

    if not projects:
        rprint("[yellow]No projects found[/yellow]")
        return

    table = Table(title="Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description", style="white")
    table.add_column("Created", style="dim")

    for project in projects:
        desc = project.description or ""
        desc_preview = desc[:50] + "..." if len(desc) > 50 else desc
        created = project.created_at.strftime("%Y-%m-%d")
        table.add_row(project.name, project.status, desc_preview, created)

    console.print(table)


@project_app.command("context")
def project_context(project_id: str = typer.Argument(..., help="Project ID")):
    """Get all memories for a project."""
    db = VaultDB()
    memories = db.get_project_memories(UUID(project_id))

    if not memories:
        rprint("[yellow]No memories found for this project[/yellow]")
        return

    rprint(f"[cyan]Project Memories:[/cyan] {len(memories)} total\n")

    for memory in memories:
        date_str = memory.created_at.strftime("%Y-%m-%d %H:%M")
        rprint(f"[dim]{date_str}[/dim] [{memory.type}]")
        rprint(f"  {memory.content}\n")


# ========== Config Commands ==========

config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show():
    """Show current configuration."""
    config = get_config()

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Embedding Provider", config.embedding_provider)
    table.add_row("Embedding Dimension", str(config.embedding_dimension))
    table.add_row("AWS Region", config.aws_region)
    table.add_row("Supabase URL", config.supabase_url[:40] + "...")
    table.add_row("Log Level", config.log_level)

    console.print(table)


@config_app.command("set-embedding")
def config_set_embedding(
    provider: str = typer.Argument(..., help="Provider name"),
    migrate: bool = typer.Option(False, help="Migrate existing embeddings"),
):
    """Change embedding provider."""
    valid_providers = ["bedrock-titan", "openai-small", "openai-large"]

    if provider not in valid_providers:
        rprint(f"[red]Invalid provider. Choose from: {', '.join(valid_providers)}[/red]")
        return

    if migrate:
        rprint("[yellow]Migration not yet implemented. Use: vault migrate[/yellow]")
        return

    rprint(f"[green]✓[/green] Embedding provider set to: {provider}")
    rprint("[dim]Note: Update your .env file to persist this change[/dim]")


# ========== Migration Commands ==========

migrate_app = typer.Typer(help="Manage embedding migrations")
app.add_typer(migrate_app, name="migrate")


@migrate_app.command("status")
def migrate_status():
    """Check migration status and model usage."""
    rprint("[cyan]Migration Status:[/cyan]")
    rprint("[yellow]Not yet implemented[/yellow]")


@migrate_app.command("run")
def migrate_run(
    to_model: str = typer.Argument(..., help="Target embedding model"),
    batch_size: int = typer.Option(100, help="Batch size"),
    dry_run: bool = typer.Option(False, help="Estimate cost without migrating"),
):
    """Migrate embeddings to a new model."""
    db = VaultDB()
    config = get_config()
    from_model = config.embedding_provider

    if from_model == to_model:
        rprint("[yellow]Source and target models are the same[/yellow]")
        return

    if dry_run:
        rprint(f"[cyan]Estimating migration: {from_model} → {to_model}[/cyan]")

    result = db.migrate_embeddings(
        from_model=from_model, to_model=to_model, batch_size=batch_size, dry_run=dry_run
    )

    if dry_run:
        rprint(f"\n[cyan]Dry Run Results:[/cyan]")
        rprint(f"  Total memories: {result['total_memories']}")
        rprint(f"  Estimated cost: ${result['estimated_cost_usd']:.4f}")
        rprint(f"\n[dim]Run without --dry-run to proceed[/dim]")
    else:
        rprint(f"\n[green]✓[/green] Migration complete!")
        rprint(f"  Migrated: {result['migrated']} memories")
        rprint(f"  From: {result['from_model']}")
        rprint(f"  To: {result['to_model']}")


if __name__ == "__main__":
    app()
