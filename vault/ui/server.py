"""Local browser UI server for Vault."""

import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..db import VaultDB
from ..models import Memory, SearchResult

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Vault UI")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _serialize_memory(memory: Memory, similarity: float | None = None) -> dict:
    data = {
        "id": str(memory.id),
        "content": memory.content,
        "type": memory.type,
        "tags": memory.tags,
        "doc_path": memory.doc_path,
        "created_at": memory.created_at.isoformat(),
    }
    if similarity is not None:
        data["similarity"] = similarity
    return data


def _parse_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/memories")
def memories(q: str | None = None, limit: int = 10, docs_only: bool = False):
    db = VaultDB()
    try:
        if q and q.strip():
            results: list[SearchResult] = db.search_memories(q.strip(), limit=limit)
            serialized = [
                _serialize_memory(result.memory, result.similarity)
                for result in results
                if not docs_only or result.memory.doc_path
            ]
        else:
            recent = db.recent_memories(limit=limit)
            serialized = [
                _serialize_memory(memory)
                for memory in recent
                if not docs_only or memory.doc_path
            ]
        return {"items": serialized}
    finally:
        db.close()


@app.get("/api/memory/{memory_id}")
def get_memory(memory_id: UUID):
    db = VaultDB()
    try:
        memory = db.get_memory(memory_id)
        if memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        return _serialize_memory(memory)
    finally:
        db.close()


@app.post("/api/memory")
def add_memory(
    content: Annotated[str, Form()],
    type: Annotated[str, Form()] = "thought",
    tags: Annotated[str | None, Form()] = None,
    extends_memory_id: Annotated[str | None, Form()] = None,
    doc: UploadFile | None = File(default=None),
):
    if not content.strip():
        raise HTTPException(status_code=400, detail="Content is required")

    temp_path: Path | None = None
    db = VaultDB()
    try:
        doc_path_arg: Path | None = None
        if doc and doc.filename:
            safe_name = Path(doc.filename).name
            suffix = Path(doc.filename).suffix
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(doc.file, tmp)
                temp_path = Path(tmp.name)
            doc_path_arg = temp_path.with_name(safe_name)
            temp_path.rename(doc_path_arg)
            temp_path = doc_path_arg

        memory = db.add_memory(
            content=content.strip(),
            type=type,
            tags=_parse_tags(tags),
            doc=doc_path_arg,
        )

        if extends_memory_id:
            db.add_memory_link(
                from_memory_id=memory.id,
                to_memory_id=UUID(extends_memory_id),
                relation_type="extends",
            )

        return _serialize_memory(memory)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
        db.close()


@app.post("/api/doc/{memory_id}/open")
def open_doc(memory_id: UUID):
    db = VaultDB()
    try:
        memory = db.get_memory(memory_id)
        if memory is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        if not memory.doc_path:
            raise HTTPException(status_code=404, detail="No document linked")

        path = Path(memory.doc_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Document file not found")

        if os.name == "nt":
            os.startfile(str(path))
        else:
            import subprocess

            subprocess.run(["xdg-open", str(path)], check=False)
        return {"ok": True, "path": str(path)}
    finally:
        db.close()
