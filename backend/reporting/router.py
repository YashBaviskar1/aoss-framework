"""
Governance Reporting API Router (Objective 1)

Provides READ-ONLY endpoints for retrieving governance reports.
Does NOT trigger report generation manually - reports are event-driven.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from reporting.report_engine import ReportEngine
from pydantic import BaseModel

router = APIRouter(prefix="/api/reports", tags=["Governance Reporting"])


# Response Models
class ReportSummary(BaseModel):
    id: str
    status: str
    created_at: str
    last_updated_at: str
    total_executions: int
    success_rate: float
    significant_events: int
    period_start: Optional[str]
    period_end: Optional[str]


class ReportDetail(BaseModel):
    id: str
    user_id: str
    report_type: str
    status: str
    created_at: str
    last_updated_at: str
    period_start: Optional[str]
    period_end: Optional[str]
    summary_stats: dict
    executions: List[dict]
    executive_summary: dict
    tags: List[str]


@router.get("/user/{user_id}", response_model=List[ReportSummary])
def get_user_reports(
    user_id: str,
    limit: int = 10,
    include_archived: bool = True,
    db: Session = Depends(get_db)
):
    """
    Retrieves all reports for a user.
    
    Returns a list of report summaries (latest first).
    This is a READ-ONLY operation.
    """
    engine = ReportEngine(db)
    reports = engine.get_user_reports(
        user_id=user_id,
        limit=limit,
        include_archived=include_archived
    )
    return reports


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves a full report by ID.
    
    Returns complete report data including:
    - Executive summary
    - All executions
    - Summary statistics
    - Timeline data
    
    This is a READ-ONLY operation.
    """
    engine = ReportEngine(db)
    report = engine.get_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.get("/user/{user_id}/active")
def get_active_report(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the currently active report for a user.
    
    This is useful for showing real-time governance status.
    """
    engine = ReportEngine(db)
    reports = engine.get_user_reports(
        user_id=user_id,
        limit=1,
        include_archived=False
    )
    
    if not reports:
        return {"message": "No active report found", "report": None}
    
    # Get full report details
    report_detail = engine.get_report(reports[0]["id"])
    return {"report": report_detail}


@router.get("/user/{user_id}/stats")
def get_user_stats(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves aggregated statistics across all user reports.
    
    Useful for dashboard widgets.
    """
    engine = ReportEngine(db)
    reports = engine.get_user_reports(
        user_id=user_id,
        limit=100,
        include_archived=True
    )
    
    # Aggregate stats
    total_executions = sum(r.get("total_executions", 0) for r in reports)
    total_significant = sum(r.get("significant_events", 0) for r in reports)
    avg_success_rate = sum(r.get("success_rate", 0) for r in reports) / len(reports) if reports else 0
    
    return {
        "total_reports": len(reports),
        "total_executions": total_executions,
        "total_significant_events": total_significant,
        "average_success_rate": round(avg_success_rate, 2),
        "active_reports": len([r for r in reports if r.get("status") == "active"])
    }


# ========== SERVER-SPECIFIC ENDPOINTS (NEW) ==========

@router.get("/{report_id}/servers")
def get_report_servers(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns list of servers involved in a report.
    
    Response includes:
    - server_id
    - server_tag (name)
    - execution_count
    - success_count
    - failure_count
    - health_status
    """
    from models import GovernanceReport, Server
    
    report = db.query(GovernanceReport).filter(
        GovernanceReport.id == report_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    executions = report.executions or []
    
    # Group by server_id
    server_stats = {}
    for exec in executions:
        server_id = exec.get('server_id')
        if not server_id:
            continue
            
        if server_id not in server_stats:
            server_stats[server_id] = {
                'server_id': server_id,
                'total_commands': 0,
                'success_count': 0,
                'failure_count': 0
            }
        
        server_stats[server_id]['total_commands'] += 1
        
        status = exec.get('status', '').lower()
        if status == 'executed' or status == 'success':
            server_stats[server_id]['success_count'] += 1
        elif status == 'failed':
            server_stats[server_id]['failure_count'] += 1
    
    # Add server names and compute health
    result = []
    for server_id, stats in server_stats.items():
        server = db.query(Server).filter(Server.id == server_id).first()
        
        success_rate = (stats['success_count'] / stats['total_commands'] * 100) if stats['total_commands'] > 0 else 0
        
        # Health status rules (improved)
        # CRITICAL: 5+ failures OR success rate below 30%
        # WARNING: 1-4 failures OR success rate 30-69%
        # HEALTHY: No failures AND success rate >= 70%
        if stats['failure_count'] >= 5 or (success_rate < 30 and stats['total_commands'] > 0):
            health_status = 'CRITICAL'
        elif stats['failure_count'] > 0 or success_rate < 70:
            health_status = 'WARNING'
        else:
            health_status = 'HEALTHY'
        
        result.append({
            'server_id': server_id,
            'server_tag': server.server_tag if server else 'Unknown',
            'execution_count': stats['total_commands'],
            'success_count': stats['success_count'],
            'failure_count': stats['failure_count'],
            'success_rate': round(success_rate, 1),
            'health_status': health_status
        })
    
    return result


@router.get("/{report_id}/servers/{server_id}")
def get_server_report(
    report_id: str,
    server_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns server-specific report with full execution timeline.
    
    Response includes:
    - Server summary (total, success, failure counts, health)
    - Full execution timeline for that server
    - Health status explanation
    """
    from models import GovernanceReport, Server
    
    report = db.query(GovernanceReport).filter(
        GovernanceReport.id == report_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    executions = report.executions or []
    
    # Filter executions for this server
    server_executions = [
        exec for exec in executions 
        if exec.get('server_id') == server_id
    ]
    
    # Compute summary
    total_commands = len(server_executions)
    success_count = sum(1 for e in server_executions if e.get('status', '').lower() in ['executed', 'success'])
    failure_count = sum(1 for e in server_executions if e.get('status', '').lower() == 'failed')
    
    success_rate = (success_count / total_commands * 100) if total_commands > 0 else 0
    
    # Health status with explanation (improved logic)
    if failure_count >= 5 or (success_rate < 30 and total_commands > 0):
        health_status = 'CRITICAL'
        health_explanation = f"Health marked CRITICAL because {failure_count} failure(s) detected (5+ failures indicates serious issues) or success rate is critically low at {success_rate:.0f}%."
    elif failure_count > 0 or success_rate < 70:
        health_status = 'WARNING'
        health_explanation = f"Health marked WARNING because {failure_count} failure(s) detected or success rate is {success_rate:.0f}% (below 70% threshold)."
    else:
        health_status = 'HEALTHY'
        health_explanation = f"Health marked HEALTHY because no failures detected and success rate is {success_rate:.0f}% (above 70% threshold)."
    
    # Format timeline
    timeline = []
    for exec in server_executions:
        timeline.append({
            'execution_log_id': exec.get('execution_log_id'),
            'timestamp': exec.get('timestamp'),
            'command': exec.get('user_command', 'N/A'),
            'status': exec.get('status', 'Unknown'),
            'summary': exec.get('summary', ''),
            'plan_steps': exec.get('plan_steps', []),
            'execution_details': exec.get('execution_details', [])
        })
    
    # Sort by timestamp (newest first)
    timeline.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return {
        'server': {
            'server_id': server_id,
            'server_tag': server.server_tag,
            'ip_address': str(server.ip_address),
            'hostname': server.hostname
        },
        'summary': {
            'total_commands': total_commands,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': round(success_rate, 1),
            'health_status': health_status,
            'health_explanation': health_explanation
        },
        'timeline': timeline
    }
