"""
Governance Reporting Engine (Objective 1)

This module is responsible for:
- Listening to execution completion events
- Fetching relevant logs, metrics, and compliance decisions
- Incrementally updating governance reports (append-only)
- Maintaining report immutability for past entries

CRITICAL: This is a READ-ONLY observer. It does NOT modify execution behavior.
"""

from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import models
from datetime import datetime, timedelta, timezone
import json


class ReportEngine:
    """
    Event-driven reporting engine that observes execution logs
    and generates incremental governance reports.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def trigger_on_execution_complete(
        self, 
        execution_log_id: str,
        user_id: str
    ) -> Dict:
        """
        Event-driven trigger: Called when an execution completes.
        
        This method:
        1. Fetches the completed execution log
        2. Extracts relevant governance data
        3. Appends to the user's active report (incremental update)
        4. Updates summary statistics
        
        Returns the updated report summary.
        """
        # Fetch execution log (READ-ONLY)
        execution_log = self.db.query(models.ExecutionLog).filter(
            models.ExecutionLog.id == execution_log_id
        ).first()
        
        if not execution_log:
            return {"error": "Execution log not found"}
        
        # Extract execution summary for report
        execution_summary = self._extract_execution_summary(execution_log)
        
        # Get or create active report for user
        report = self._get_or_create_active_report(user_id)
        
        # Append execution to report (incremental update)
        self._append_execution_to_report(report, execution_summary)
        
        # Update summary statistics
        self._update_summary_stats(report)
        
        self.db.commit()
        
        return {
            "report_id": str(report.id),
            "executions_count": len(report.executions),
            "last_updated": report.last_updated_at.isoformat()
        }
    
    def _extract_execution_summary(self, execution_log: models.ExecutionLog) -> Dict:
        """
        Extracts governance-relevant data from an execution log.
        
        Returns a structured summary containing:
        - User command
        - Plan steps
        - Executed commands
        - Compliance decisions (if any)
        - Execution outcome
        - Duration
        - Significant events
        """
        # Parse execution results (stored as a list of step results)
        execution_results = execution_log.execution_results or []
        plan = execution_log.plan or []
        
        # Determine if this is a significant event
        is_significant = self._is_significant_event(execution_log)
        
        # Extract compliance decisions (if present in results)
        compliance_decisions = []
        for result in execution_results:
            if isinstance(result, dict) and "compliance_check" in result:
                compliance_decisions.append(result["compliance_check"])
        
        # Calculate duration (if available)
        duration = None
        if execution_results:
            # Check if any result has timing info
            for result in execution_results:
                if isinstance(result, dict) and result.get("duration"):
                    duration = result.get("duration")
                    break
        
        summary = {
            "execution_log_id": str(execution_log.id),
            "timestamp": execution_log.created_at.isoformat(),
            "user_command": execution_log.query,
            "status": execution_log.status,
            "plan_steps_count": len(plan),
            "compliance_decisions": compliance_decisions,
            "outcome": execution_log.status,
            "duration_seconds": duration,
            "is_significant": is_significant,
            "server_id": str(execution_log.server_id),
            "summary": execution_log.agent_summary or "No summary available"
        }
        
        # Add detailed steps only for significant events
        if is_significant:
            summary["plan_steps"] = plan
            summary["execution_details"] = execution_results
        
        return summary
    
    def _is_significant_event(self, execution_log: models.ExecutionLog) -> bool:
        """
        Determines if an execution is significant enough to include
        detailed information in the report.
        
        Significant events include:
        - Deployments
        - Configuration changes
        - Policy blocks
        - Failed executions
        - Long-running operations
        """
        query_lower = execution_log.query.lower()
        
        # Keywords indicating significant operations
        significant_keywords = [
            "deploy", "deployment", "install", "configure", 
            "setup", "create", "delete", "remove", "restart",
            "nginx", "docker", "database", "service"
        ]
        
        # Check for significant keywords
        if any(keyword in query_lower for keyword in significant_keywords):
            return True
        
        # Failed executions are always significant
        if execution_log.status in ["Failed", "Blocked"]:
            return True
        
        # Check execution results for policy blocks
        if execution_log.execution_results:
            if execution_log.execution_results.get("blocked_by_policy"):
                return True
        
        return False
    
    def _get_or_create_active_report(self, user_id: str) -> models.GovernanceReport:
        """
        Gets the active report for a user, or creates a new one if none exists.
        
        Reports are kept active for a rolling window (default: 30 days).
        After that, they are archived and a new report is created.
        """
        # Try to get active report
        active_report = self.db.query(models.GovernanceReport).filter(
            models.GovernanceReport.user_id == user_id,
            models.GovernanceReport.status == "active"
        ).order_by(models.GovernanceReport.created_at.desc()).first()
        
        # Create new report if none exists or current is too old
        if not active_report or self._should_archive_report(active_report):
            if active_report:
                active_report.status = "archived"
                active_report.period_end = datetime.now(timezone.utc)
            
            active_report = models.GovernanceReport(
                user_id=user_id,
                report_type="activity",
                status="active",
                executions=[],
                summary_stats={
                    "total_executions": 0,
                    "successful": 0,
                    "failed": 0,
                    "blocked": 0,
                    "significant_events": 0
                },
                period_start=datetime.now(timezone.utc),
                tags=[]
            )
            self.db.add(active_report)
            self.db.flush()
        
        return active_report
    
    def _should_archive_report(self, report: models.GovernanceReport) -> bool:
        """
        Determines if a report should be archived based on age or size.
        
        Default policy:
        - Archive after 30 days
        - Archive if more than 1000 executions
        """
        age_threshold = timedelta(days=30)
        size_threshold = 1000
        
        report_age = datetime.now(timezone.utc) - report.created_at
        execution_count = len(report.executions) if report.executions else 0
        
        return report_age > age_threshold or execution_count >= size_threshold
    
    def _append_execution_to_report(
        self, 
        report: models.GovernanceReport, 
        execution_summary: Dict
    ):
        """
        Appends an execution summary to the report (incremental update).
        
        IMPORTANT: This is append-only. Past entries remain unchanged.
        """
        from sqlalchemy.orm.attributes import flag_modified
        
        if not report.executions:
            report.executions = []
        
        # Append new execution (immutable for past entries)
        report.executions.append(execution_summary)
        
        # CRITICAL: Mark the JSON column as modified so SQLAlchemy tracks the change
        flag_modified(report, 'executions')
        
        # Mark report as updated
        report.last_updated_at = datetime.now(timezone.utc)
    
    def _update_summary_stats(self, report: models.GovernanceReport):
        """
        Recalculates summary statistics for the report.
        
        This provides aggregated metrics for quick insights.
        """
        from sqlalchemy.orm.attributes import flag_modified
        
        executions = report.executions or []
        
        stats = {
            "total_executions": len(executions),
            "successful": sum(1 for e in executions if e.get("status") == "Executed"),
            "failed": sum(1 for e in executions if e.get("status") == "Failed"),
            "blocked": sum(1 for e in executions if e.get("status") == "Blocked"),
            "significant_events": sum(1 for e in executions if e.get("is_significant", False)),
            "total_compliance_checks": sum(len(e.get("compliance_decisions", [])) for e in executions),
        }
        
        # Calculate success rate
        if stats["total_executions"] > 0:
            stats["success_rate"] = round(
                (stats["successful"] / stats["total_executions"]) * 100, 2
            )
        else:
            stats["success_rate"] = 0.0
        
        report.summary_stats = stats
        
        # CRITICAL: Mark the JSON column as modified
        flag_modified(report, 'summary_stats')
    
    def get_report(self, report_id: str) -> Optional[Dict]:
        """
        Retrieves a full report by ID.
        
        Returns structured report data for UI rendering.
        """
        report = self.db.query(models.GovernanceReport).filter(
            models.GovernanceReport.id == report_id
        ).first()
        
        if not report:
            return None
        
        return self._format_report_for_ui(report)
    
    def get_user_reports(
        self, 
        user_id: str, 
        limit: int = 10,
        include_archived: bool = True
    ) -> List[Dict]:
        """
        Retrieves all reports for a user.
        
        Returns a list of report summaries (latest first).
        """
        query = self.db.query(models.GovernanceReport).filter(
            models.GovernanceReport.user_id == user_id
        )
        
        if not include_archived:
            query = query.filter(models.GovernanceReport.status == "active")
        
        reports = query.order_by(
            models.GovernanceReport.created_at.desc()
        ).limit(limit).all()
        
        return [self._format_report_summary(r) for r in reports]
    
    def _format_report_for_ui(self, report: models.GovernanceReport) -> Dict:
        """
        Formats a full report for UI consumption.
        
        Includes:
        - Executive summary
        - All executions (with filtering options)
        - Summary statistics
        - Timeline view data
        """
        return {
            "id": str(report.id),
            "user_id": report.user_id,
            "report_type": report.report_type,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "last_updated_at": report.last_updated_at.isoformat(),
            "period_start": report.period_start.isoformat() if report.period_start else None,
            "period_end": report.period_end.isoformat() if report.period_end else None,
            "summary_stats": report.summary_stats or {},
            "executions": report.executions or [],
            "executive_summary": self._generate_executive_summary(report),
            "tags": report.tags or []
        }
    
    def _format_report_summary(self, report: models.GovernanceReport) -> Dict:
        """
        Formats a report summary for list view.
        """
        stats = report.summary_stats or {}
        
        return {
            "id": str(report.id),
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "last_updated_at": report.last_updated_at.isoformat(),
            "total_executions": stats.get("total_executions", 0),
            "success_rate": stats.get("success_rate", 0),
            "significant_events": stats.get("significant_events", 0),
            "period_start": report.period_start.isoformat() if report.period_start else None,
            "period_end": report.period_end.isoformat() if report.period_end else None
        }
    
    def _generate_executive_summary(self, report: models.GovernanceReport) -> Dict:
        """
        Generates an auto-computed executive summary.
        
        Provides high-level insights about the report period.
        """
        stats = report.summary_stats or {}
        executions = report.executions or []
        
        # Find most common operations
        operation_types = {}
        for exec_data in executions:
            cmd = exec_data.get("user_command", "").lower()
            # Simple categorization
            if "install" in cmd or "setup" in cmd:
                category = "Installation & Setup"
            elif "deploy" in cmd:
                category = "Deployment"
            elif "configure" in cmd or "config" in cmd:
                category = "Configuration"
            elif "check" in cmd or "status" in cmd or "list" in cmd:
                category = "Monitoring & Inspection"
            else:
                category = "Other Operations"
            
            operation_types[category] = operation_types.get(category, 0) + 1
        
        # Get significant events
        significant = [e for e in executions if e.get("is_significant", False)]
        
        return {
            "total_activities": stats.get("total_executions", 0),
            "success_rate": f"{stats.get('success_rate', 0)}%",
            "failed_count": stats.get("failed", 0),
            "blocked_count": stats.get("blocked", 0),
            "operation_breakdown": operation_types,
            "significant_events_count": len(significant),
            "compliance_checks_performed": stats.get("total_compliance_checks", 0),
            "report_health": self._calculate_report_health(stats)
        }
    
    def _calculate_report_health(self, stats: Dict) -> str:
        """
        Calculates overall report health indicator.
        
        Returns: "healthy", "warning", or "critical"
        """
        success_rate = stats.get("success_rate", 0)
        blocked_count = stats.get("blocked", 0)
        failed_count = stats.get("failed", 0)
        
        if success_rate >= 90 and blocked_count == 0:
            return "healthy"
        elif success_rate >= 70 or (blocked_count > 0 and blocked_count <= 2):
            return "warning"
        else:
            return "critical"
