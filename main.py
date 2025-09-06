# main.py
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Query, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict
import json
import asyncio

from database import models, schemas
from database.session import engine, get_db
from database.log import logger
from monitoring import runner  # import the updated runner.py

app = FastAPI(title="AOSS Observability API", version="1.1.0")

# --- Startup Event ---
@app.on_event("startup")
async def startup():
    # Create tables
    models.Base.metadata.create_all(bind=engine)

    # Start the monitoring loop in the background
    loop = asyncio.get_event_loop()
    loop.create_task(runner.monitor_loop())
    print("Background monitoring loop started")

# --- Root Endpoint ---
@app.get("/")
async def root():
    return {"message": "AOSS Observability API", "version": app.version}

# --- Prometheus Metrics ---
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# --- Create Log Entry ---
@app.post("/logs/", response_model=schemas.LogEntry, status_code=201)
async def create_log_entry(request: schemas.LogEntryCreate, db: Session = Depends(get_db)):
    try:
        log_obj = logger.log(
            agent_role=request.agent_role,
            status=request.status,
            message=request.message,
            payload=request.payload,
            rag_context_ids=request.rag_context_ids,
            task_id=request.task_id,
            trace_id=request.trace_id,
            step_id=request.step_id,
            duration_ms=request.duration_ms,
            db=db
        )
        return schemas.LogEntry.from_orm(log_obj)
    except Exception as e:
        import traceback
        print("❌ Error in create_log_entry:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create log entry")

# --- Query Logs ---
@app.get("/logs/", response_model=Dict)
async def get_logs(
    agent_role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    trace_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    limit: int = Query(100, gt=0, le=1000),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(models.LogEntry)
        if agent_role:
            query = query.filter(models.LogEntry.agent_role == agent_role)
        if status:
            query = query.filter(models.LogEntry.status.ilike(f"%{status}%"))
        if trace_id:
            query = query.filter(models.LogEntry.trace_id == trace_id)
        if task_id:
            query = query.filter(models.LogEntry.task_id == task_id)
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            query = query.filter(models.LogEntry.timestamp >= start_dt)
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            query = query.filter(models.LogEntry.timestamp <= end_dt)

        total_count = query.count()
        orm_logs = query.order_by(models.LogEntry.timestamp.desc()).limit(limit).all()
        results = [schemas.LogEntry.from_orm(l).dict() for l in orm_logs]
        return {"logs": results, "count": len(results), "has_more": total_count > limit}
    except ValueError as e:
        raise HTTPException(400, f"Invalid datetime: {str(e)}")
    except Exception as e:
        import traceback
        print("❌ Error in get_logs:", e)
        traceback.print_exc()
        raise HTTPException(500, "Internal server error")

# --- Export Logs ---
@app.get("/logs/export")
async def export_logs(
    db: Session = Depends(get_db),
    agent_role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None)
):
    try:
        query = db.query(models.LogEntry)
        if agent_role:
            query = query.filter(models.LogEntry.agent_role == agent_role)
        if status:
            query = query.filter(models.LogEntry.status == status)
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            query = query.filter(models.LogEntry.timestamp >= start_dt)
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            query = query.filter(models.LogEntry.timestamp <= end_dt)

        logs = query.order_by(models.LogEntry.timestamp.asc()).all()

        def generate():
            for l in logs:
                entry = schemas.LogEntry.from_orm(l).dict()
                yield json.dumps(entry, default=str) + "\n"

        filename = f"logs_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
        from fastapi.responses import StreamingResponse
        return StreamingResponse(generate(), media_type="application/x-ndjson",
                                 headers={"Content-Disposition": f"attachment; filename={filename}"})
    except Exception as e:
        import traceback
        print("❌ Error in export_logs:", e)
        traceback.print_exc()
        raise HTTPException(500, "Export failed")
