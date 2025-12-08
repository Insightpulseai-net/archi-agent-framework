"""
Notebook Endpoints
==================
CRUD operations for notebooks and cell execution.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class CellContent(BaseModel):
    id: str
    type: str  # 'code', 'markdown', 'sql'
    source: str
    outputs: List[dict] = []
    metadata: dict = {}


class NotebookCreate(BaseModel):
    name: str
    description: Optional[str] = None
    path: Optional[str] = None
    cells: List[CellContent] = []
    tags: List[str] = []


class NotebookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cells: Optional[List[CellContent]] = None
    tags: Optional[List[str]] = None


class NotebookResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    path: Optional[str]
    cells: List[CellContent]
    tags: List[str]
    version: int
    created_by: Optional[str]
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class NotebookListItem(BaseModel):
    id: str
    name: str
    description: Optional[str]
    path: Optional[str]
    tags: List[str]
    version: int
    updated_at: datetime


class CellExecuteRequest(BaseModel):
    notebook_id: str
    cell_id: str
    cell_type: str
    source: str
    connection_id: Optional[str] = None


class CellExecuteResponse(BaseModel):
    cell_id: str
    status: str
    outputs: List[dict]
    execution_time_ms: int


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[NotebookListItem])
async def list_notebooks(
    path: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all notebooks with optional filtering.
    """
    from app.models.notebook import Notebook

    query = select(Notebook)

    # Apply filters
    if path:
        query = query.where(Notebook.path.startswith(path))

    if tags:
        tag_list = tags.split(",")
        query = query.where(Notebook.tags.overlap(tag_list))

    if search:
        query = query.where(
            Notebook.name.ilike(f"%{search}%") |
            Notebook.description.ilike(f"%{search}%")
        )

    # Pagination
    query = query.offset(offset).limit(limit)
    query = query.order_by(Notebook.updated_at.desc())

    result = await db.execute(query)
    notebooks = result.scalars().all()

    return [
        NotebookListItem(
            id=str(nb.id),
            name=nb.name,
            description=nb.description,
            path=nb.path,
            tags=nb.tags or [],
            version=nb.version,
            updated_at=nb.updated_at,
        )
        for nb in notebooks
    ]


@router.post("", response_model=NotebookResponse, status_code=status.HTTP_201_CREATED)
async def create_notebook(
    notebook: NotebookCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new notebook.
    """
    from app.models.notebook import Notebook

    db_notebook = Notebook(
        name=notebook.name,
        description=notebook.description,
        path=notebook.path,
        content={"cells": [cell.model_dump() for cell in notebook.cells]},
        tags=notebook.tags,
        created_by=current_user["id"],
        updated_by=current_user["id"],
    )

    db.add(db_notebook)
    await db.commit()
    await db.refresh(db_notebook)

    return NotebookResponse(
        id=str(db_notebook.id),
        name=db_notebook.name,
        description=db_notebook.description,
        path=db_notebook.path,
        cells=[CellContent(**cell) for cell in db_notebook.content.get("cells", [])],
        tags=db_notebook.tags or [],
        version=db_notebook.version,
        created_by=str(db_notebook.created_by) if db_notebook.created_by else None,
        updated_by=str(db_notebook.updated_by) if db_notebook.updated_by else None,
        created_at=db_notebook.created_at,
        updated_at=db_notebook.updated_at,
    )


@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(
    notebook_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a notebook by ID.
    """
    from app.models.notebook import Notebook

    result = await db.execute(
        select(Notebook).where(Notebook.id == notebook_id)
    )
    notebook = result.scalar_one_or_none()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    return NotebookResponse(
        id=str(notebook.id),
        name=notebook.name,
        description=notebook.description,
        path=notebook.path,
        cells=[CellContent(**cell) for cell in notebook.content.get("cells", [])],
        tags=notebook.tags or [],
        version=notebook.version,
        created_by=str(notebook.created_by) if notebook.created_by else None,
        updated_by=str(notebook.updated_by) if notebook.updated_by else None,
        created_at=notebook.created_at,
        updated_at=notebook.updated_at,
    )


@router.put("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(
    notebook_id: UUID,
    update: NotebookUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a notebook.
    """
    from app.models.notebook import Notebook, NotebookVersion

    result = await db.execute(
        select(Notebook).where(Notebook.id == notebook_id)
    )
    notebook = result.scalar_one_or_none()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Save version before update
    version_record = NotebookVersion(
        notebook_id=notebook.id,
        version=notebook.version,
        content=notebook.content,
        created_by=current_user["id"],
    )
    db.add(version_record)

    # Apply updates
    if update.name is not None:
        notebook.name = update.name
    if update.description is not None:
        notebook.description = update.description
    if update.cells is not None:
        notebook.content = {"cells": [cell.model_dump() for cell in update.cells]}
    if update.tags is not None:
        notebook.tags = update.tags

    notebook.version += 1
    notebook.updated_by = current_user["id"]

    await db.commit()
    await db.refresh(notebook)

    return NotebookResponse(
        id=str(notebook.id),
        name=notebook.name,
        description=notebook.description,
        path=notebook.path,
        cells=[CellContent(**cell) for cell in notebook.content.get("cells", [])],
        tags=notebook.tags or [],
        version=notebook.version,
        created_by=str(notebook.created_by) if notebook.created_by else None,
        updated_by=str(notebook.updated_by) if notebook.updated_by else None,
        created_at=notebook.created_at,
        updated_at=notebook.updated_at,
    )


@router.delete("/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notebook(
    notebook_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a notebook.
    """
    from app.models.notebook import Notebook

    result = await db.execute(
        select(Notebook).where(Notebook.id == notebook_id)
    )
    notebook = result.scalar_one_or_none()

    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    await db.delete(notebook)
    await db.commit()


@router.get("/{notebook_id}/versions")
async def list_notebook_versions(
    notebook_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List version history for a notebook.
    """
    from app.models.notebook import NotebookVersion

    result = await db.execute(
        select(NotebookVersion)
        .where(NotebookVersion.notebook_id == notebook_id)
        .order_by(NotebookVersion.version.desc())
    )
    versions = result.scalars().all()

    return [
        {
            "version": v.version,
            "created_at": v.created_at,
            "created_by": str(v.created_by) if v.created_by else None,
        }
        for v in versions
    ]
