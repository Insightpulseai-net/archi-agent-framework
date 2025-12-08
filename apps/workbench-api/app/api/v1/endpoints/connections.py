"""
Connection Endpoints
====================
Data source connection management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user, require_role

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class ConnectionConfig(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    url: Optional[str] = None
    extra: dict = {}


class ConnectionCreate(BaseModel):
    name: str
    type: str  # postgresql, mysql, odoo_rpc, odoo_rest, rest_api, sftp, s3, superset, ocr_service
    config: ConnectionConfig
    username: Optional[str] = None
    password: Optional[str] = None


class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[ConnectionConfig] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class ConnectionResponse(BaseModel):
    id: str
    name: str
    type: str
    config: dict
    is_active: bool
    last_tested_at: Optional[str]
    last_test_status: Optional[str]
    created_at: str
    updated_at: str


class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[int] = None
    details: dict = {}


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[ConnectionResponse])
async def list_connections(
    type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all connections.
    """
    from app.models.connection import Connection

    query = select(Connection)

    if type:
        query = query.where(Connection.type == type)

    if is_active is not None:
        query = query.where(Connection.is_active == is_active)

    query = query.order_by(Connection.name)

    result = await db.execute(query)
    connections = result.scalars().all()

    return [
        ConnectionResponse(
            id=str(c.id),
            name=c.name,
            type=c.type,
            config=c.config,
            is_active=c.is_active,
            last_tested_at=c.last_tested_at.isoformat() if c.last_tested_at else None,
            last_test_status=c.last_test_status,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in connections
    ]


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection: ConnectionCreate,
    current_user: dict = Depends(require_role(["engineer", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new connection.
    """
    from app.models.connection import Connection
    from app.services.encryption import encrypt_credentials

    # Encrypt credentials if provided
    credentials_encrypted = None
    if connection.username or connection.password:
        credentials_encrypted = encrypt_credentials({
            "username": connection.username,
            "password": connection.password,
        })

    db_connection = Connection(
        name=connection.name,
        type=connection.type,
        config=connection.config.model_dump(),
        credentials_encrypted=credentials_encrypted,
        created_by=current_user["id"],
    )

    db.add(db_connection)
    await db.commit()
    await db.refresh(db_connection)

    return ConnectionResponse(
        id=str(db_connection.id),
        name=db_connection.name,
        type=db_connection.type,
        config=db_connection.config,
        is_active=db_connection.is_active,
        last_tested_at=None,
        last_test_status=None,
        created_at=db_connection.created_at.isoformat(),
        updated_at=db_connection.updated_at.isoformat(),
    )


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a connection by ID.
    """
    from app.models.connection import Connection

    result = await db.execute(
        select(Connection).where(Connection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return ConnectionResponse(
        id=str(connection.id),
        name=connection.name,
        type=connection.type,
        config=connection.config,
        is_active=connection.is_active,
        last_tested_at=connection.last_tested_at.isoformat() if connection.last_tested_at else None,
        last_test_status=connection.last_test_status,
        created_at=connection.created_at.isoformat(),
        updated_at=connection.updated_at.isoformat(),
    )


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: UUID,
    update: ConnectionUpdate,
    current_user: dict = Depends(require_role(["engineer", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a connection.
    """
    from app.models.connection import Connection
    from app.services.encryption import encrypt_credentials

    result = await db.execute(
        select(Connection).where(Connection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    if update.name is not None:
        connection.name = update.name
    if update.config is not None:
        connection.config = update.config.model_dump()
    if update.is_active is not None:
        connection.is_active = update.is_active

    # Update credentials if provided
    if update.username is not None or update.password is not None:
        connection.credentials_encrypted = encrypt_credentials({
            "username": update.username,
            "password": update.password,
        })

    await db.commit()
    await db.refresh(connection)

    return ConnectionResponse(
        id=str(connection.id),
        name=connection.name,
        type=connection.type,
        config=connection.config,
        is_active=connection.is_active,
        last_tested_at=connection.last_tested_at.isoformat() if connection.last_tested_at else None,
        last_test_status=connection.last_test_status,
        created_at=connection.created_at.isoformat(),
        updated_at=connection.updated_at.isoformat(),
    )


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a connection.
    """
    from app.models.connection import Connection

    result = await db.execute(
        select(Connection).where(Connection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    await db.delete(connection)
    await db.commit()


@router.post("/{connection_id}/test", response_model=ConnectionTestResult)
async def test_connection(
    connection_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Test a connection.
    """
    from datetime import datetime
    from app.models.connection import Connection
    from app.services.connection_tester import test_connection as run_test

    result = await db.execute(
        select(Connection).where(Connection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Run the test
    test_result = await run_test(connection)

    # Update connection with test results
    connection.last_tested_at = datetime.utcnow()
    connection.last_test_status = "success" if test_result.success else "failed"
    await db.commit()

    return test_result


@router.get("/{connection_id}/schemas")
async def list_connection_schemas(
    connection_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List available schemas/databases for a connection.
    """
    from app.models.connection import Connection
    from app.services.schema_discovery import discover_schemas

    result = await db.execute(
        select(Connection).where(Connection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    schemas = await discover_schemas(connection)

    return {"schemas": schemas}


@router.get("/{connection_id}/tables")
async def list_connection_tables(
    connection_id: UUID,
    schema: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List tables for a connection.
    """
    from app.models.connection import Connection
    from app.services.schema_discovery import discover_tables

    result = await db.execute(
        select(Connection).where(Connection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    tables = await discover_tables(connection, schema)

    return {"tables": tables}
