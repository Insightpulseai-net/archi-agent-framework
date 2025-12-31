# apps/pulser-hub/handlers/databricks.py
"""Databricks job handler for Docs2Code pipeline execution.

Manages the 7-notebook Docs2Code pipeline in Databricks:
1. 01_ingest_documents - RAG ingestion (~30 min)
2. 02_analyze_gaps - Gap analysis (~15 min)
3. 03_generate_modules - Code generation (~20 min)
4. 04_validate_compliance - BIR compliance (~10 min)
5. 05_run_tests - Test execution (~10 min)
6. 06_deploy_staging - Staging deployment (~10 min)
7. 07_deploy_production - Production deployment (~5 min)
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class PipelineAction(str, Enum):
    """Available pipeline actions."""

    RUN_FULL_PIPELINE = "run_full_pipeline"
    RUN_INGESTION = "run_ingestion"
    RUN_ANALYSIS = "run_analysis"
    RUN_GENERATION = "run_generation"
    RUN_COMPLIANCE = "run_compliance"
    RUN_TESTS = "run_tests"
    RUN_DEPLOYMENT = "run_deployment"


class RunStatus(str, Enum):
    """Databricks run status values."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    SKIPPED = "SKIPPED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class NotebookConfig:
    """Configuration for a Databricks notebook."""

    path: str
    timeout_seconds: int
    base_parameters: dict


# Notebook configuration for Docs2Code pipeline
NOTEBOOK_CONFIGS: dict[str, NotebookConfig] = {
    "ingestion": NotebookConfig(
        path="/Workspace/Docs2Code/01_ingest_documents",
        timeout_seconds=1800,  # 30 minutes
        base_parameters={
            "source_type": "all",
            "vector_store": "supabase",
        },
    ),
    "analysis": NotebookConfig(
        path="/Workspace/Docs2Code/02_analyze_gaps",
        timeout_seconds=900,  # 15 minutes
        base_parameters={
            "comparison_mode": "full",
        },
    ),
    "generation": NotebookConfig(
        path="/Workspace/Docs2Code/03_generate_modules",
        timeout_seconds=1200,  # 20 minutes
        base_parameters={
            "target_version": "odoo18",
            "80_20_rule": "true",
        },
    ),
    "compliance": NotebookConfig(
        path="/Workspace/Docs2Code/04_validate_compliance",
        timeout_seconds=600,  # 10 minutes
        base_parameters={
            "tax_year": "2024",
            "form_count": "36",
        },
    ),
    "tests": NotebookConfig(
        path="/Workspace/Docs2Code/05_run_tests",
        timeout_seconds=600,  # 10 minutes
        base_parameters={
            "test_type": "unit",
            "coverage_threshold": "80",
        },
    ),
    "staging": NotebookConfig(
        path="/Workspace/Docs2Code/06_deploy_staging",
        timeout_seconds=600,  # 10 minutes
        base_parameters={
            "environment": "staging",
            "auto_upgrade": "true",
        },
    ),
    "production": NotebookConfig(
        path="/Workspace/Docs2Code/07_deploy_production",
        timeout_seconds=300,  # 5 minutes
        base_parameters={
            "environment": "production",
            "require_approval": "true",
        },
    ),
}

# Action to notebook mapping
ACTION_NOTEBOOKS: dict[PipelineAction, list[str]] = {
    PipelineAction.RUN_FULL_PIPELINE: [
        "ingestion", "analysis", "generation", "compliance", "tests", "staging"
    ],
    PipelineAction.RUN_INGESTION: ["ingestion"],
    PipelineAction.RUN_ANALYSIS: ["analysis"],
    PipelineAction.RUN_GENERATION: ["generation"],
    PipelineAction.RUN_COMPLIANCE: ["compliance"],
    PipelineAction.RUN_TESTS: ["tests"],
    PipelineAction.RUN_DEPLOYMENT: ["staging"],
}


class DatabricksJobHandler:
    """Handler for Databricks job execution.

    Manages notebook execution, status tracking, and result aggregation
    for the Docs2Code pipeline.
    """

    def __init__(
        self,
        workspace_url: str = None,
        token: str = None,
        cluster_id: str = None,
    ):
        """Initialize the Databricks handler.

        Args:
            workspace_url: Databricks workspace URL
            token: Personal access token or service principal token
            cluster_id: Default cluster ID for job execution
        """
        self.workspace_url = (
            workspace_url or
            os.getenv("DATABRICKS_WORKSPACE_URL", "https://adb-1234567890.azuredatabricks.net")
        )
        self.token = token or os.getenv("DATABRICKS_TOKEN")
        self.cluster_id = cluster_id or os.getenv("DATABRICKS_CLUSTER_ID")

        # Active runs tracking
        self._active_runs: dict[str, dict] = {}

    @property
    def _headers(self) -> dict[str, str]:
        """Get HTTP headers for Databricks API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def run_pipeline(
        self,
        action: PipelineAction,
        parameters: Optional[dict] = None,
        notify_on_complete: bool = True,
    ) -> dict[str, Any]:
        """Execute a pipeline action.

        Args:
            action: The pipeline action to execute
            parameters: Optional override parameters
            notify_on_complete: Whether to send completion notification

        Returns:
            Run information including run_id
        """
        notebooks = ACTION_NOTEBOOKS.get(action, [])
        if not notebooks:
            raise ValueError(f"Unknown action: {action}")

        run_id = f"run-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Calculate estimated completion time
        total_seconds = sum(
            NOTEBOOK_CONFIGS[nb].timeout_seconds
            for nb in notebooks
        )
        estimated_minutes = total_seconds // 60

        # Store run info
        self._active_runs[run_id] = {
            "action": action.value,
            "notebooks": notebooks,
            "current_index": 0,
            "status": "RUNNING",
            "started_at": datetime.utcnow().isoformat(),
            "parameters": parameters or {},
            "notify_on_complete": notify_on_complete,
            "notebook_runs": {},
        }

        # Start first notebook
        first_notebook = notebooks[0]
        await self._run_notebook(run_id, first_notebook, parameters)

        return {
            "run_id": run_id,
            "action": action.value,
            "status": "RUNNING",
            "message": f"Started {action.value} with {len(notebooks)} notebook(s)",
            "started_at": datetime.utcnow().isoformat(),
            "estimated_completion": f"{estimated_minutes} minutes",
            "progress": {
                "current_notebook": first_notebook,
                "completed": 0,
                "total": len(notebooks),
                "percentage": 0,
            },
        }

    async def _run_notebook(
        self,
        run_id: str,
        notebook_name: str,
        override_params: Optional[dict] = None,
    ) -> dict:
        """Execute a single notebook.

        Args:
            run_id: Parent run ID
            notebook_name: Name of notebook to run
            override_params: Parameters to override defaults

        Returns:
            Databricks run response
        """
        config = NOTEBOOK_CONFIGS.get(notebook_name)
        if not config:
            raise ValueError(f"Unknown notebook: {notebook_name}")

        # Merge parameters
        params = {**config.base_parameters}
        if override_params:
            params.update(override_params)

        # Build run request
        request_body = {
            "run_name": f"{run_id}-{notebook_name}",
            "existing_cluster_id": self.cluster_id,
            "notebook_task": {
                "notebook_path": config.path,
                "base_parameters": params,
            },
            "timeout_seconds": config.timeout_seconds,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.workspace_url}/api/2.1/jobs/runs/submit",
                headers=self._headers,
                json=request_body,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

            # Track notebook run
            self._active_runs[run_id]["notebook_runs"][notebook_name] = {
                "databricks_run_id": result["run_id"],
                "status": "RUNNING",
                "started_at": datetime.utcnow().isoformat(),
            }

            return result

    async def get_run_status(self, run_id: str) -> dict[str, Any]:
        """Get the status of a pipeline run.

        Args:
            run_id: The run ID to check

        Returns:
            Current run status
        """
        if run_id not in self._active_runs:
            return {
                "run_id": run_id,
                "status": "NOT_FOUND",
                "message": "Run ID not found",
            }

        run_info = self._active_runs[run_id]
        notebooks = run_info["notebooks"]
        current_index = run_info["current_index"]

        # Check status of current notebook
        if current_index < len(notebooks):
            current_notebook = notebooks[current_index]
            notebook_run = run_info["notebook_runs"].get(current_notebook, {})
            databricks_run_id = notebook_run.get("databricks_run_id")

            if databricks_run_id:
                status = await self._get_databricks_run_status(databricks_run_id)
                notebook_run["status"] = status["state"]["life_cycle_state"]

                # Check if completed
                if status["state"]["life_cycle_state"] == "TERMINATED":
                    result_state = status["state"].get("result_state", "SUCCESS")
                    notebook_run["result"] = result_state
                    notebook_run["completed_at"] = datetime.utcnow().isoformat()

                    if result_state == "SUCCESS":
                        # Move to next notebook
                        run_info["current_index"] += 1
                        if run_info["current_index"] < len(notebooks):
                            next_notebook = notebooks[run_info["current_index"]]
                            await self._run_notebook(
                                run_id,
                                next_notebook,
                                run_info["parameters"],
                            )
                        else:
                            run_info["status"] = "COMPLETED"
                            run_info["completed_at"] = datetime.utcnow().isoformat()
                    else:
                        run_info["status"] = "FAILED"
                        run_info["error"] = f"Notebook {current_notebook} failed"

        completed = sum(
            1 for nb in notebooks
            if run_info["notebook_runs"].get(nb, {}).get("result") == "SUCCESS"
        )

        return {
            "run_id": run_id,
            "status": run_info["status"],
            "progress": {
                "current_notebook": notebooks[min(current_index, len(notebooks) - 1)],
                "completed": completed,
                "total": len(notebooks),
                "percentage": round(completed / len(notebooks) * 100, 1),
            },
            "started_at": run_info["started_at"],
            "completed_at": run_info.get("completed_at"),
            "notebook_runs": run_info["notebook_runs"],
        }

    async def _get_databricks_run_status(self, databricks_run_id: int) -> dict:
        """Get status of a Databricks run.

        Args:
            databricks_run_id: Databricks run ID

        Returns:
            Run status response
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.workspace_url}/api/2.1/jobs/runs/get",
                headers=self._headers,
                params={"run_id": databricks_run_id},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def cancel_run(self, run_id: str) -> dict:
        """Cancel a running pipeline.

        Args:
            run_id: The run ID to cancel

        Returns:
            Cancellation result
        """
        if run_id not in self._active_runs:
            return {"status": "NOT_FOUND", "message": "Run ID not found"}

        run_info = self._active_runs[run_id]

        # Cancel all active Databricks runs
        for notebook_name, notebook_run in run_info["notebook_runs"].items():
            if notebook_run.get("status") == "RUNNING":
                databricks_run_id = notebook_run.get("databricks_run_id")
                if databricks_run_id:
                    await self._cancel_databricks_run(databricks_run_id)
                notebook_run["status"] = "CANCELLED"

        run_info["status"] = "CANCELLED"
        run_info["cancelled_at"] = datetime.utcnow().isoformat()

        return {
            "run_id": run_id,
            "status": "CANCELLED",
            "message": "Pipeline cancelled successfully",
        }

    async def _cancel_databricks_run(self, databricks_run_id: int) -> dict:
        """Cancel a Databricks run.

        Args:
            databricks_run_id: Databricks run ID

        Returns:
            Cancellation response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.workspace_url}/api/2.1/jobs/runs/cancel",
                headers=self._headers,
                json={"run_id": databricks_run_id},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
