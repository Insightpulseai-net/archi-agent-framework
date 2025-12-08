"""
Integration Endpoints
=====================
External service integrations (Odoo, Superset, OCR, Agents).
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user, require_role

router = APIRouter()


# ============================================================================
# Odoo Integration
# ============================================================================

class OdooQueryRequest(BaseModel):
    model: str
    domain: list = []
    fields: List[str] = []
    limit: int = 100
    offset: int = 0
    order: Optional[str] = None


class OdooCreateRequest(BaseModel):
    model: str
    values: dict


class OdooUpdateRequest(BaseModel):
    model: str
    record_id: int
    values: dict


@router.get("/odoo/models")
async def list_odoo_models(
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    List available Odoo models.
    """
    from app.services.odoo_client import get_odoo_client

    client = get_odoo_client()
    models = await client.list_models(search)

    return {"models": models}


@router.post("/odoo/query")
async def query_odoo(
    request: OdooQueryRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Query Odoo data.
    """
    from app.services.odoo_client import get_odoo_client

    client = get_odoo_client()

    try:
        result = await client.search_read(
            model=request.model,
            domain=request.domain,
            fields=request.fields,
            limit=request.limit,
            offset=request.offset,
            order=request.order,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"records": result, "count": len(result)}


@router.post("/odoo/create")
async def create_odoo_record(
    request: OdooCreateRequest,
    current_user: dict = Depends(require_role(["engineer", "admin"])),
):
    """
    Create a record in Odoo.
    """
    from app.services.odoo_client import get_odoo_client

    client = get_odoo_client()

    try:
        record_id = await client.create(
            model=request.model,
            values=request.values,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"id": record_id}


@router.put("/odoo/update")
async def update_odoo_record(
    request: OdooUpdateRequest,
    current_user: dict = Depends(require_role(["engineer", "admin"])),
):
    """
    Update a record in Odoo.
    """
    from app.services.odoo_client import get_odoo_client

    client = get_odoo_client()

    try:
        await client.write(
            model=request.model,
            record_id=request.record_id,
            values=request.values,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"success": True}


# ============================================================================
# Superset Integration
# ============================================================================

@router.get("/superset/datasets")
async def list_superset_datasets(
    current_user: dict = Depends(get_current_user),
):
    """
    List Superset datasets.
    """
    from app.services.superset_client import get_superset_client

    client = get_superset_client()
    datasets = await client.list_datasets()

    return {"datasets": datasets}


@router.post("/superset/datasets/{dataset_id}/refresh")
async def refresh_superset_dataset(
    dataset_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger dataset refresh in Superset.
    """
    from app.services.superset_client import get_superset_client

    client = get_superset_client()

    try:
        await client.refresh_dataset(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Refresh triggered"}


@router.get("/superset/dashboards")
async def list_superset_dashboards(
    current_user: dict = Depends(get_current_user),
):
    """
    List Superset dashboards.
    """
    from app.services.superset_client import get_superset_client

    client = get_superset_client()
    dashboards = await client.list_dashboards()

    return {"dashboards": dashboards}


# ============================================================================
# OCR Integration
# ============================================================================

class OCRResponse(BaseModel):
    document_id: str
    status: str
    confidence: Optional[float] = None
    extracted_data: Optional[dict] = None
    raw_text: Optional[str] = None


@router.post("/ocr/extract", response_model=OCRResponse)
async def extract_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and extract data from a document using OCR.
    """
    from app.services.ocr_client import get_ocr_client
    from app.services.storage import upload_file
    import uuid

    # Upload file to storage
    document_id = str(uuid.uuid4())
    storage_url = await upload_file(file, document_id)

    # Call OCR service
    client = get_ocr_client()

    try:
        result = await client.extract(
            file_url=storage_url,
            document_type=document_type,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Store in Bronze layer
    from app.models.bronze import Document, OCRExtraction

    doc = Document(
        id=document_id,
        storage_url=storage_url,
        file_name=file.filename,
        mime_type=file.content_type,
        source="upload",
    )
    db.add(doc)

    extraction = OCRExtraction(
        document_id=document_id,
        ocr_engine="paddleocr",
        raw_text=result.get("raw_text"),
        raw_regions=result.get("regions"),
        confidence_score=result.get("confidence"),
    )
    db.add(extraction)

    await db.commit()

    return OCRResponse(
        document_id=document_id,
        status="completed",
        confidence=result.get("confidence"),
        extracted_data=result.get("extracted_data"),
        raw_text=result.get("raw_text"),
    )


@router.get("/ocr/{document_id}", response_model=OCRResponse)
async def get_ocr_result(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get OCR extraction result.
    """
    from app.models.bronze import Document, OCRExtraction
    from sqlalchemy import select

    result = await db.execute(
        select(Document, OCRExtraction)
        .join(OCRExtraction, Document.id == OCRExtraction.document_id)
        .where(Document.id == document_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    doc, extraction = row

    return OCRResponse(
        document_id=str(doc.id),
        status="completed",
        confidence=float(extraction.confidence_score) if extraction.confidence_score else None,
        raw_text=extraction.raw_text,
    )


# ============================================================================
# Agent Integration
# ============================================================================

class AgentTaskRequest(BaseModel):
    agent: str  # odoo-developer, finance-ssc, devops, bi-architect
    task_type: str
    payload: dict
    priority: str = "normal"


class AgentTaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None


@router.post("/agents/dispatch", response_model=AgentTaskResponse)
async def dispatch_agent_task(
    request: AgentTaskRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Dispatch a task to an AI agent.
    """
    from app.services.agent_client import dispatch_to_agent
    import uuid

    task_id = str(uuid.uuid4())

    try:
        result = await dispatch_to_agent(
            agent=request.agent,
            task_type=request.task_type,
            payload=request.payload,
            task_id=task_id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AgentTaskResponse(
        task_id=task_id,
        status="completed" if result else "dispatched",
        result=result,
    )


@router.get("/agents/status/{task_id}", response_model=AgentTaskResponse)
async def get_agent_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get status of an agent task.
    """
    from app.services.agent_client import get_task_status

    result = await get_task_status(task_id)

    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

    return AgentTaskResponse(
        task_id=task_id,
        status=result.get("status", "unknown"),
        result=result.get("result"),
    )


# ============================================================================
# n8n Webhook Bridge
# ============================================================================

class N8NWebhookRequest(BaseModel):
    workflow_id: str
    data: dict


@router.post("/n8n/trigger")
async def trigger_n8n_workflow(
    request: N8NWebhookRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger an n8n workflow via webhook.
    """
    import httpx

    if not settings.N8N_WEBHOOK_URL:
        raise HTTPException(status_code=400, detail="n8n webhook URL not configured")

    webhook_url = f"{settings.N8N_WEBHOOK_URL}/{request.workflow_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                webhook_url,
                json=request.data,
                headers={"X-API-Key": settings.N8N_API_KEY} if settings.N8N_API_KEY else {},
                timeout=30,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=400, detail=f"n8n webhook failed: {str(e)}")

    return {"status": "triggered", "response": response.json() if response.text else None}
