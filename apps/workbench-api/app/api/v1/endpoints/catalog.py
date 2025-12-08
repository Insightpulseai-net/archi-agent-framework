"""
Data Catalog Endpoints
======================
Browse and search data assets.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    description: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False


class CatalogEntryCreate(BaseModel):
    connection_id: str
    entry_type: str  # table, view, file, api_endpoint
    schema_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    columns: List[ColumnInfo] = []
    classification: str = "internal"
    tags: List[str] = []


class CatalogEntryUpdate(BaseModel):
    description: Optional[str] = None
    classification: Optional[str] = None
    tags: Optional[List[str]] = None


class CatalogEntryResponse(BaseModel):
    id: str
    connection_id: Optional[str]
    entry_type: str
    schema_name: Optional[str]
    name: str
    description: Optional[str]
    columns: List[ColumnInfo]
    row_count: Optional[int]
    size_bytes: Optional[int]
    classification: str
    tags: List[str]
    last_scanned_at: Optional[str]
    created_at: str
    updated_at: str


class CatalogSearchResult(BaseModel):
    id: str
    entry_type: str
    schema_name: Optional[str]
    name: str
    description: Optional[str]
    classification: str
    tags: List[str]
    relevance_score: float


class DataPreviewResponse(BaseModel):
    columns: List[str]
    rows: List[List]
    row_count: int
    truncated: bool


class LineageResponse(BaseModel):
    entry_id: str
    entry_name: str
    upstream: List[dict]
    downstream: List[dict]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[CatalogEntryResponse])
async def list_catalog_entries(
    connection_id: Optional[UUID] = None,
    entry_type: Optional[str] = None,
    schema_name: Optional[str] = None,
    classification: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List catalog entries with filtering.
    """
    from app.models.catalog import CatalogEntry

    query = select(CatalogEntry)

    if connection_id:
        query = query.where(CatalogEntry.connection_id == connection_id)
    if entry_type:
        query = query.where(CatalogEntry.entry_type == entry_type)
    if schema_name:
        query = query.where(CatalogEntry.schema_name == schema_name)
    if classification:
        query = query.where(CatalogEntry.classification == classification)
    if tags:
        tag_list = tags.split(",")
        query = query.where(CatalogEntry.tags.overlap(tag_list))

    query = query.offset(offset).limit(limit)
    query = query.order_by(CatalogEntry.schema_name, CatalogEntry.name)

    result = await db.execute(query)
    entries = result.scalars().all()

    return [
        CatalogEntryResponse(
            id=str(e.id),
            connection_id=str(e.connection_id) if e.connection_id else None,
            entry_type=e.entry_type,
            schema_name=e.schema_name,
            name=e.name,
            description=e.description,
            columns=[ColumnInfo(**c) for c in e.columns] if e.columns else [],
            row_count=e.row_count,
            size_bytes=e.size_bytes,
            classification=e.classification,
            tags=e.tags or [],
            last_scanned_at=e.last_scanned_at.isoformat() if e.last_scanned_at else None,
            created_at=e.created_at.isoformat(),
            updated_at=e.updated_at.isoformat(),
        )
        for e in entries
    ]


@router.get("/search", response_model=List[CatalogSearchResult])
async def search_catalog(
    q: str = Query(..., min_length=2),
    entry_type: Optional[str] = None,
    classification: Optional[str] = None,
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Full-text search across catalog entries.
    """
    from app.models.catalog import CatalogEntry

    # Build search query with ts_rank for relevance
    search_query = func.to_tsquery('english', q.replace(' ', ' & '))

    query = select(
        CatalogEntry,
        func.ts_rank(
            func.to_tsvector('english',
                func.coalesce(CatalogEntry.name, '') + ' ' +
                func.coalesce(CatalogEntry.description, '')
            ),
            search_query
        ).label('rank')
    ).where(
        func.to_tsvector('english',
            func.coalesce(CatalogEntry.name, '') + ' ' +
            func.coalesce(CatalogEntry.description, '')
        ).op('@@')(search_query)
    )

    if entry_type:
        query = query.where(CatalogEntry.entry_type == entry_type)
    if classification:
        query = query.where(CatalogEntry.classification == classification)

    query = query.order_by(func.ts_rank(
        func.to_tsvector('english',
            func.coalesce(CatalogEntry.name, '') + ' ' +
            func.coalesce(CatalogEntry.description, '')
        ),
        search_query
    ).desc()).limit(limit)

    result = await db.execute(query)
    results = result.all()

    return [
        CatalogSearchResult(
            id=str(entry.id),
            entry_type=entry.entry_type,
            schema_name=entry.schema_name,
            name=entry.name,
            description=entry.description,
            classification=entry.classification,
            tags=entry.tags or [],
            relevance_score=float(rank),
        )
        for entry, rank in results
    ]


@router.get("/{entry_id}", response_model=CatalogEntryResponse)
async def get_catalog_entry(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a catalog entry by ID.
    """
    from app.models.catalog import CatalogEntry

    result = await db.execute(
        select(CatalogEntry).where(CatalogEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Catalog entry not found")

    return CatalogEntryResponse(
        id=str(entry.id),
        connection_id=str(entry.connection_id) if entry.connection_id else None,
        entry_type=entry.entry_type,
        schema_name=entry.schema_name,
        name=entry.name,
        description=entry.description,
        columns=[ColumnInfo(**c) for c in entry.columns] if entry.columns else [],
        row_count=entry.row_count,
        size_bytes=entry.size_bytes,
        classification=entry.classification,
        tags=entry.tags or [],
        last_scanned_at=entry.last_scanned_at.isoformat() if entry.last_scanned_at else None,
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat(),
    )


@router.put("/{entry_id}", response_model=CatalogEntryResponse)
async def update_catalog_entry(
    entry_id: UUID,
    update: CatalogEntryUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update catalog entry metadata.
    """
    from app.models.catalog import CatalogEntry

    result = await db.execute(
        select(CatalogEntry).where(CatalogEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Catalog entry not found")

    if update.description is not None:
        entry.description = update.description
    if update.classification is not None:
        entry.classification = update.classification
    if update.tags is not None:
        entry.tags = update.tags

    await db.commit()
    await db.refresh(entry)

    return CatalogEntryResponse(
        id=str(entry.id),
        connection_id=str(entry.connection_id) if entry.connection_id else None,
        entry_type=entry.entry_type,
        schema_name=entry.schema_name,
        name=entry.name,
        description=entry.description,
        columns=[ColumnInfo(**c) for c in entry.columns] if entry.columns else [],
        row_count=entry.row_count,
        size_bytes=entry.size_bytes,
        classification=entry.classification,
        tags=entry.tags or [],
        last_scanned_at=entry.last_scanned_at.isoformat() if entry.last_scanned_at else None,
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat(),
    )


@router.get("/{entry_id}/preview", response_model=DataPreviewResponse)
async def preview_catalog_entry(
    entry_id: UUID,
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Preview data for a catalog entry.
    """
    from app.models.catalog import CatalogEntry
    from app.services.data_preview import get_preview

    result = await db.execute(
        select(CatalogEntry).where(CatalogEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Catalog entry not found")

    # Check classification - restrict preview for confidential/restricted
    if entry.classification in ["restricted"]:
        if current_user["role"] not in ["admin"]:
            raise HTTPException(
                status_code=403,
                detail="Preview not allowed for restricted data"
            )

    preview = await get_preview(entry, limit)

    return preview


@router.get("/{entry_id}/lineage", response_model=LineageResponse)
async def get_catalog_entry_lineage(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get lineage information for a catalog entry.
    """
    from app.models.catalog import CatalogEntry, Lineage

    result = await db.execute(
        select(CatalogEntry).where(CatalogEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Catalog entry not found")

    # Get upstream (sources)
    upstream_result = await db.execute(
        select(Lineage, CatalogEntry)
        .join(CatalogEntry, Lineage.source_entry_id == CatalogEntry.id)
        .where(Lineage.target_entry_id == entry_id)
    )
    upstream = upstream_result.all()

    # Get downstream (targets)
    downstream_result = await db.execute(
        select(Lineage, CatalogEntry)
        .join(CatalogEntry, Lineage.target_entry_id == CatalogEntry.id)
        .where(Lineage.source_entry_id == entry_id)
    )
    downstream = downstream_result.all()

    return LineageResponse(
        entry_id=str(entry.id),
        entry_name=entry.name,
        upstream=[
            {
                "id": str(source.id),
                "name": source.name,
                "schema_name": source.schema_name,
                "transformation_type": lineage.transformation_type,
            }
            for lineage, source in upstream
        ],
        downstream=[
            {
                "id": str(target.id),
                "name": target.name,
                "schema_name": target.schema_name,
                "transformation_type": lineage.transformation_type,
            }
            for lineage, target in downstream
        ],
    )


@router.post("/scan/{connection_id}")
async def scan_connection(
    connection_id: UUID,
    schema: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Scan a connection and update catalog.
    """
    from app.models.connection import Connection
    from app.services.catalog_scanner import scan_connection as run_scan

    result = await db.execute(
        select(Connection).where(Connection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Run scan (this could be async/background)
    scan_result = await run_scan(connection, schema, db)

    return {
        "message": "Scan complete",
        "entries_created": scan_result.get("created", 0),
        "entries_updated": scan_result.get("updated", 0),
    }
