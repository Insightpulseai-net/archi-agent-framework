"""
Execution Endpoints
===================
Cell execution and query execution.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class SQLExecuteRequest(BaseModel):
    sql: str
    connection_id: str
    parameters: dict = {}
    limit: int = 1000


class PythonExecuteRequest(BaseModel):
    code: str
    context: dict = {}


class ExecuteResponse(BaseModel):
    status: str  # success, error
    execution_time_ms: int
    outputs: list
    error: Optional[str] = None


class QueryResult(BaseModel):
    columns: list
    rows: list
    row_count: int
    truncated: bool
    execution_time_ms: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/sql", response_model=QueryResult)
async def execute_sql(
    request: SQLExecuteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute SQL query against a connection.
    """
    import time
    from app.models.connection import Connection
    from app.services.query_executor import execute_sql_query
    from app.services.encryption import decrypt_credentials
    from sqlalchemy import select

    # Get connection
    result = await db.execute(
        select(Connection).where(Connection.id == request.connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Decrypt credentials
    credentials = None
    if connection.credentials_encrypted:
        credentials = decrypt_credentials(connection.credentials_encrypted)

    # Execute query
    start_time = time.time()

    try:
        query_result = await execute_sql_query(
            connection=connection,
            credentials=credentials,
            sql=request.sql,
            parameters=request.parameters,
            limit=request.limit,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    execution_time_ms = int((time.time() - start_time) * 1000)

    # Log access for audit
    from app.services.audit import log_data_access
    await log_data_access(
        user_id=current_user["id"],
        connection_id=request.connection_id,
        query_type="sql",
        rows_accessed=query_result.row_count,
        db=db,
    )

    return QueryResult(
        columns=query_result.columns,
        rows=query_result.rows,
        row_count=query_result.row_count,
        truncated=query_result.truncated,
        execution_time_ms=execution_time_ms,
    )


@router.post("/python", response_model=ExecuteResponse)
async def execute_python(
    request: PythonExecuteRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Execute Python code in a sandboxed environment.
    """
    import time
    from app.services.python_executor import execute_python_code

    start_time = time.time()

    try:
        result = await execute_python_code(
            code=request.code,
            context=request.context,
        )
        status = "success"
        error = None
    except Exception as e:
        result = []
        status = "error"
        error = str(e)

    execution_time_ms = int((time.time() - start_time) * 1000)

    return ExecuteResponse(
        status=status,
        execution_time_ms=execution_time_ms,
        outputs=result,
        error=error,
    )


@router.post("/duckdb", response_model=QueryResult)
async def execute_duckdb(
    request: SQLExecuteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute SQL query using DuckDB (local OLAP engine).
    """
    import time
    from app.services.duckdb_executor import execute_duckdb_query

    start_time = time.time()

    try:
        query_result = await execute_duckdb_query(
            sql=request.sql,
            parameters=request.parameters,
            limit=request.limit,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    execution_time_ms = int((time.time() - start_time) * 1000)

    return QueryResult(
        columns=query_result.columns,
        rows=query_result.rows,
        row_count=query_result.row_count,
        truncated=query_result.truncated,
        execution_time_ms=execution_time_ms,
    )


# ============================================================================
# WebSocket for streaming execution
# ============================================================================

@router.websocket("/ws/execute")
async def websocket_execute(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for streaming cell execution.
    """
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            execution_type = data.get("type")
            payload = data.get("payload", {})

            if execution_type == "sql":
                async for chunk in stream_sql_execution(payload, db):
                    await websocket.send_json(chunk)

            elif execution_type == "python":
                async for chunk in stream_python_execution(payload):
                    await websocket.send_json(chunk)

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown execution type: {execution_type}"
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close()


async def stream_sql_execution(payload: dict, db: AsyncSession):
    """Stream SQL execution results."""
    from app.services.query_executor import stream_sql_query

    yield {"type": "start", "message": "Executing SQL..."}

    try:
        async for row_batch in stream_sql_query(payload):
            yield {"type": "data", "rows": row_batch}

        yield {"type": "complete", "message": "Query complete"}

    except Exception as e:
        yield {"type": "error", "message": str(e)}


async def stream_python_execution(payload: dict):
    """Stream Python execution output."""
    from app.services.python_executor import stream_python_code

    yield {"type": "start", "message": "Executing Python..."}

    try:
        async for output in stream_python_code(payload.get("code", "")):
            yield {"type": "output", "data": output}

        yield {"type": "complete", "message": "Execution complete"}

    except Exception as e:
        yield {"type": "error", "message": str(e)}
