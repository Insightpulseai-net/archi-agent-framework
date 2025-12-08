"""
Pipeline Endpoints
==================
Pipeline management and execution.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user, require_role

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class PipelineTask(BaseModel):
    id: str
    name: str
    type: str  # 'sql', 'python', 'http', 'odoo', 'superset'
    config: dict
    depends_on: List[str] = []


class PipelineDefinition(BaseModel):
    tasks: List[PipelineTask]
    parameters: dict = {}
    error_handling: dict = {}


class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    definition: PipelineDefinition
    schedule: Optional[str] = None  # cron expression
    tags: List[str] = []


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[PipelineDefinition] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class PipelineResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    definition: dict
    schedule: Optional[str]
    is_active: bool
    last_run_at: Optional[datetime]
    last_run_status: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class PipelineRunCreate(BaseModel):
    parameters: dict = {}


class PipelineRunResponse(BaseModel):
    id: str
    pipeline_id: str
    status: str
    trigger_type: str
    parameters: dict
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    error_message: Optional[str]


class PipelineTaskStatus(BaseModel):
    task_name: str
    task_type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    error_message: Optional[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[PipelineResponse])
async def list_pipelines(
    is_active: Optional[bool] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all pipelines.
    """
    from app.models.pipeline import Pipeline

    query = select(Pipeline)

    if is_active is not None:
        query = query.where(Pipeline.is_active == is_active)

    if tags:
        tag_list = tags.split(",")
        query = query.where(Pipeline.tags.overlap(tag_list))

    if search:
        query = query.where(
            Pipeline.name.ilike(f"%{search}%") |
            Pipeline.description.ilike(f"%{search}%")
        )

    query = query.offset(offset).limit(limit)
    query = query.order_by(Pipeline.updated_at.desc())

    result = await db.execute(query)
    pipelines = result.scalars().all()

    return [
        PipelineResponse(
            id=str(p.id),
            name=p.name,
            description=p.description,
            definition=p.definition,
            schedule=p.schedule,
            is_active=p.is_active,
            last_run_at=p.last_run_at,
            last_run_status=p.last_run_status,
            tags=p.tags or [],
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in pipelines
    ]


@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    pipeline: PipelineCreate,
    current_user: dict = Depends(require_role(["developer", "engineer", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new pipeline.
    """
    from app.models.pipeline import Pipeline

    db_pipeline = Pipeline(
        name=pipeline.name,
        description=pipeline.description,
        definition=pipeline.definition.model_dump(),
        schedule=pipeline.schedule,
        tags=pipeline.tags,
        created_by=current_user["id"],
        updated_by=current_user["id"],
    )

    db.add(db_pipeline)
    await db.commit()
    await db.refresh(db_pipeline)

    return PipelineResponse(
        id=str(db_pipeline.id),
        name=db_pipeline.name,
        description=db_pipeline.description,
        definition=db_pipeline.definition,
        schedule=db_pipeline.schedule,
        is_active=db_pipeline.is_active,
        last_run_at=db_pipeline.last_run_at,
        last_run_status=db_pipeline.last_run_status,
        tags=db_pipeline.tags or [],
        created_at=db_pipeline.created_at,
        updated_at=db_pipeline.updated_at,
    )


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a pipeline by ID.
    """
    from app.models.pipeline import Pipeline

    result = await db.execute(
        select(Pipeline).where(Pipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return PipelineResponse(
        id=str(pipeline.id),
        name=pipeline.name,
        description=pipeline.description,
        definition=pipeline.definition,
        schedule=pipeline.schedule,
        is_active=pipeline.is_active,
        last_run_at=pipeline.last_run_at,
        last_run_status=pipeline.last_run_status,
        tags=pipeline.tags or [],
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
    )


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: UUID,
    update: PipelineUpdate,
    current_user: dict = Depends(require_role(["developer", "engineer", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a pipeline.
    """
    from app.models.pipeline import Pipeline

    result = await db.execute(
        select(Pipeline).where(Pipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if update.name is not None:
        pipeline.name = update.name
    if update.description is not None:
        pipeline.description = update.description
    if update.definition is not None:
        pipeline.definition = update.definition.model_dump()
    if update.schedule is not None:
        pipeline.schedule = update.schedule
    if update.is_active is not None:
        pipeline.is_active = update.is_active
    if update.tags is not None:
        pipeline.tags = update.tags

    pipeline.updated_by = current_user["id"]

    await db.commit()
    await db.refresh(pipeline)

    return PipelineResponse(
        id=str(pipeline.id),
        name=pipeline.name,
        description=pipeline.description,
        definition=pipeline.definition,
        schedule=pipeline.schedule,
        is_active=pipeline.is_active,
        last_run_at=pipeline.last_run_at,
        last_run_status=pipeline.last_run_status,
        tags=pipeline.tags or [],
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
    )


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: UUID,
    current_user: dict = Depends(require_role(["engineer", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a pipeline.
    """
    from app.models.pipeline import Pipeline

    result = await db.execute(
        select(Pipeline).where(Pipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    await db.delete(pipeline)
    await db.commit()


@router.post("/{pipeline_id}/run", response_model=PipelineRunResponse)
async def trigger_pipeline_run(
    pipeline_id: UUID,
    run_request: PipelineRunCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["developer", "engineer", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a pipeline run.
    """
    from app.models.pipeline import Pipeline, PipelineRun
    from app.services.pipeline_executor import execute_pipeline

    result = await db.execute(
        select(Pipeline).where(Pipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    # Create run record
    run = PipelineRun(
        pipeline_id=pipeline_id,
        trigger_type="manual",
        parameters=run_request.parameters,
        triggered_by=current_user["id"],
    )

    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Execute in background
    background_tasks.add_task(
        execute_pipeline,
        str(run.id),
        pipeline.definition,
        run_request.parameters,
    )

    return PipelineRunResponse(
        id=str(run.id),
        pipeline_id=str(run.pipeline_id),
        status=run.status,
        trigger_type=run.trigger_type,
        parameters=run.parameters,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
    )


@router.get("/{pipeline_id}/runs", response_model=List[PipelineRunResponse])
async def list_pipeline_runs(
    pipeline_id: UUID,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List runs for a pipeline.
    """
    from app.models.pipeline import PipelineRun

    query = select(PipelineRun).where(PipelineRun.pipeline_id == pipeline_id)

    if status:
        query = query.where(PipelineRun.status == status)

    query = query.offset(offset).limit(limit)
    query = query.order_by(PipelineRun.created_at.desc())

    result = await db.execute(query)
    runs = result.scalars().all()

    return [
        PipelineRunResponse(
            id=str(r.id),
            pipeline_id=str(r.pipeline_id),
            status=r.status,
            trigger_type=r.trigger_type,
            parameters=r.parameters,
            started_at=r.started_at,
            completed_at=r.completed_at,
            duration_ms=r.duration_ms,
            error_message=r.error_message,
        )
        for r in runs
    ]


@router.get("/runs/{run_id}/tasks", response_model=List[PipelineTaskStatus])
async def get_run_task_status(
    run_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get task-level status for a pipeline run.
    """
    from app.models.pipeline import PipelineTask

    result = await db.execute(
        select(PipelineTask)
        .where(PipelineTask.run_id == run_id)
        .order_by(PipelineTask.created_at)
    )
    tasks = result.scalars().all()

    return [
        PipelineTaskStatus(
            task_name=t.task_name,
            task_type=t.task_type,
            status=t.status,
            started_at=t.started_at,
            completed_at=t.completed_at,
            duration_ms=t.duration_ms,
            error_message=t.error_message,
        )
        for t in tasks
    ]


@router.post("/runs/{run_id}/cancel")
async def cancel_pipeline_run(
    run_id: UUID,
    current_user: dict = Depends(require_role(["developer", "engineer", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a running pipeline.
    """
    from app.models.pipeline import PipelineRun

    result = await db.execute(
        select(PipelineRun).where(PipelineRun.id == run_id)
    )
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    if run.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel run with status: {run.status}"
        )

    run.status = "cancelled"
    run.completed_at = datetime.utcnow()

    await db.commit()

    return {"message": "Pipeline run cancelled"}
