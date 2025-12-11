"""Test Engine API - FastAPI application."""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from . import __version__

# Configuration
class Settings(BaseSettings):
    service_name: str = "test-engine"
    service_port: int = 8081
    log_level: str = "INFO"
    device_engine_url: str = Field(
        default="http://localhost:8080", alias="DEVICE_ENGINE_URL"
    )
    influxdb_url: str = Field(default="http://localhost:8086", alias="INFLUXDB_URL")
    influxdb_token: str = Field(default="", alias="INFLUXDB_TOKEN")
    influxdb_org: str = Field(default="iotix", alias="INFLUXDB_ORG")
    influxdb_bucket: str = Field(default="telemetry", alias="INFLUXDB_BUCKET")

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Track startup time
start_time = time.time()


# Models
class TestStatus:
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"


class TestSuiteConfig(BaseModel):
    """Configuration for a test suite."""
    name: str
    description: str | None = None
    test_cases: list[str] = Field(alias="testCases")
    tags: list[str] = []
    timeout_seconds: int = Field(3600, alias="timeoutSeconds")


class TestRunRequest(BaseModel):
    """Request to execute a test run."""
    suite_id: str | None = Field(None, alias="suiteId")
    test_cases: list[str] | None = Field(None, alias="testCases")
    device_group_id: str | None = Field(None, alias="deviceGroupId")
    variables: dict[str, Any] = {}
    tags: list[str] = []


class TestRunResult(BaseModel):
    """Result of a test run."""
    run_id: str = Field(alias="runId")
    status: str
    started_at: datetime = Field(alias="startedAt")
    finished_at: datetime | None = Field(None, alias="finishedAt")
    duration_seconds: float | None = Field(None, alias="durationSeconds")
    total_tests: int = Field(0, alias="totalTests")
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    results: list[dict[str, Any]] = []

    model_config = {"populate_by_name": True}


class ScheduleConfig(BaseModel):
    """Configuration for scheduled test execution."""
    cron: str
    suite_id: str = Field(alias="suiteId")
    enabled: bool = True
    notification_url: str | None = Field(None, alias="notificationUrl")


# In-memory storage (would be a database in production)
test_suites: dict[str, TestSuiteConfig] = {}
test_runs: dict[str, TestRunResult] = {}
schedules: dict[str, ScheduleConfig] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Test Engine...")
    yield
    logger.info("Test Engine shutdown complete")


app = FastAPI(
    title="IoTix Test Engine",
    description="Test execution and automation engine for IoT simulation",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health endpoints
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Check service health."""
    return {
        "status": "healthy",
        "version": __version__,
        "uptimeSeconds": time.time() - start_time,
        "activeSuites": len(test_suites),
        "activeRuns": sum(1 for r in test_runs.values() if r.status == TestStatus.RUNNING),
    }


@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict[str, str]:
    """Check if service is ready."""
    return {"status": "ready"}


# Test Suite endpoints
@app.get("/api/v1/suites", tags=["Suites"])
async def list_suites() -> list[dict[str, Any]]:
    """List all test suites."""
    return [s.model_dump(by_alias=True) for s in test_suites.values()]


@app.post("/api/v1/suites", status_code=201, tags=["Suites"])
async def create_suite(suite: TestSuiteConfig) -> dict[str, Any]:
    """Create a new test suite."""
    suite_id = f"suite-{uuid4().hex[:8]}"
    test_suites[suite_id] = suite
    return {"id": suite_id, **suite.model_dump(by_alias=True)}


@app.get("/api/v1/suites/{suite_id}", tags=["Suites"])
async def get_suite(suite_id: str) -> dict[str, Any]:
    """Get a test suite by ID."""
    if suite_id not in test_suites:
        raise HTTPException(status_code=404, detail=f"Suite not found: {suite_id}")
    return {"id": suite_id, **test_suites[suite_id].model_dump(by_alias=True)}


@app.delete("/api/v1/suites/{suite_id}", status_code=204, tags=["Suites"])
async def delete_suite(suite_id: str) -> None:
    """Delete a test suite."""
    if suite_id not in test_suites:
        raise HTTPException(status_code=404, detail=f"Suite not found: {suite_id}")
    del test_suites[suite_id]


# Test Run endpoints
@app.get("/api/v1/runs", tags=["Runs"])
async def list_runs(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=500),
) -> list[dict[str, Any]]:
    """List test runs."""
    runs = list(test_runs.values())
    if status:
        runs = [r for r in runs if r.status == status]
    runs.sort(key=lambda r: r.started_at, reverse=True)
    return [r.model_dump(by_alias=True) for r in runs[:limit]]


@app.post("/api/v1/runs", status_code=201, tags=["Runs"])
async def create_run(
    request: TestRunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Create and start a new test run."""
    run_id = f"run-{uuid4().hex[:8]}"

    result = TestRunResult(
        run_id=run_id,
        status=TestStatus.PENDING,
        started_at=datetime.now(timezone.utc),
    )
    test_runs[run_id] = result

    # Start test execution in background
    background_tasks.add_task(execute_test_run, run_id, request)

    return result.model_dump(by_alias=True)


@app.get("/api/v1/runs/{run_id}", tags=["Runs"])
async def get_run(run_id: str) -> dict[str, Any]:
    """Get test run details."""
    if run_id not in test_runs:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return test_runs[run_id].model_dump(by_alias=True)


@app.post("/api/v1/runs/{run_id}/cancel", tags=["Runs"])
async def cancel_run(run_id: str) -> dict[str, Any]:
    """Cancel a running test."""
    if run_id not in test_runs:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    run = test_runs[run_id]
    if run.status == TestStatus.RUNNING:
        run.status = TestStatus.CANCELLED
        run.finished_at = datetime.now(timezone.utc)
    return run.model_dump(by_alias=True)


@app.get("/api/v1/runs/{run_id}/report", tags=["Runs"])
async def get_run_report(
    run_id: str,
    format: str = Query("json", enum=["json", "html", "junit", "csv", "markdown"]),
) -> Any:
    """Get test run report in various formats."""
    from fastapi.responses import PlainTextResponse, HTMLResponse

    from .reports import (
        generate_html_report,
        generate_junit_report,
        generate_csv_report,
        generate_markdown_report,
    )

    if run_id not in test_runs:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    run = test_runs[run_id]
    run_dict = run.model_dump(by_alias=True)

    if format == "json":
        return run_dict
    elif format == "html":
        return HTMLResponse(content=generate_html_report(run_dict))
    elif format == "junit":
        return PlainTextResponse(
            content=generate_junit_report(run_dict),
            media_type="application/xml",
        )
    elif format == "csv":
        return PlainTextResponse(
            content=generate_csv_report(run_dict),
            media_type="text/csv",
        )
    elif format == "markdown":
        return PlainTextResponse(
            content=generate_markdown_report(run_dict),
            media_type="text/markdown",
        )


# Schedule endpoints
@app.get("/api/v1/schedules", tags=["Schedules"])
async def list_schedules() -> list[dict[str, Any]]:
    """List all scheduled test executions."""
    return [
        {"id": k, **v.model_dump(by_alias=True)}
        for k, v in schedules.items()
    ]


@app.post("/api/v1/schedules", status_code=201, tags=["Schedules"])
async def create_schedule(config: ScheduleConfig) -> dict[str, Any]:
    """Create a scheduled test execution."""
    schedule_id = f"schedule-{uuid4().hex[:8]}"
    schedules[schedule_id] = config
    return {"id": schedule_id, **config.model_dump(by_alias=True)}


@app.delete("/api/v1/schedules/{schedule_id}", status_code=204, tags=["Schedules"])
async def delete_schedule(schedule_id: str) -> None:
    """Delete a scheduled test execution."""
    if schedule_id not in schedules:
        raise HTTPException(status_code=404, detail=f"Schedule not found: {schedule_id}")
    del schedules[schedule_id]


# Webhook endpoint for CI/CD
@app.post("/api/v1/webhook", tags=["Webhook"])
async def webhook_trigger(
    request: TestRunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Trigger test execution via webhook."""
    return await create_run(request, background_tasks)


# Helper functions
async def execute_test_run(run_id: str, request: TestRunRequest) -> None:
    """Execute a test run (background task)."""
    run = test_runs.get(run_id)
    if not run:
        return

    run.status = TestStatus.RUNNING
    logger.info(f"Starting test run: {run_id}")

    try:
        # Simulate test execution
        import asyncio
        await asyncio.sleep(2)  # Simulated test time

        # Update results
        run.status = TestStatus.PASSED
        run.finished_at = datetime.now(timezone.utc)
        run.duration_seconds = (run.finished_at - run.started_at).total_seconds()
        run.total_tests = 5
        run.passed = 5
        run.results = [
            {"name": "test_device_creation", "status": "passed", "duration": 0.5},
            {"name": "test_telemetry_generation", "status": "passed", "duration": 0.8},
            {"name": "test_mqtt_connectivity", "status": "passed", "duration": 0.3},
            {"name": "test_device_group_start", "status": "passed", "duration": 1.2},
            {"name": "test_device_metrics", "status": "passed", "duration": 0.4},
        ]

        logger.info(f"Test run completed: {run_id} - {run.status}")

    except Exception as e:
        run.status = TestStatus.ERROR
        run.finished_at = datetime.now(timezone.utc)
        run.duration_seconds = (run.finished_at - run.started_at).total_seconds()
        logger.error(f"Test run failed: {run_id} - {e}")


