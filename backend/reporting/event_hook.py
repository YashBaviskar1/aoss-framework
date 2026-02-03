"""
Event Hook for Governance Reporting (Objective 1)

This module provides a non-intrusive hook that observes execution
completion events and triggers report generation.

CRITICAL: This is an observer only. It does NOT modify execution behavior.
"""

from sqlalchemy.orm import Session
from reporting.report_engine import ReportEngine
import logging

logger = logging.getLogger(__name__)


class ReportingEventHook:
    """
    Event-driven hook for governance reporting.
    
    This class provides a clean interface for triggering report
    updates when executions complete.
    
    Usage:
        After an execution completes, call:
        trigger_report_update(execution_log_id, user_id, db)
    """
    
    @staticmethod
    def trigger_report_update(
        execution_log_id: str,
        user_id: str,
        db: Session
    ) -> dict:
        """
        Triggers an incremental report update after execution completion.
        
        This is the main entry point for event-driven reporting.
        
        Args:
            execution_log_id: UUID of the completed execution log
            user_id: User who initiated the execution
            db: Database session
        
        Returns:
            Dictionary with update status
        """
        try:
            engine = ReportEngine(db)
            result = engine.trigger_on_execution_complete(
                execution_log_id=execution_log_id,
                user_id=user_id
            )
            
            logger.info(
                f"Report updated for user {user_id}, "
                f"execution {execution_log_id}"
            )
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logger.error(
                f"Failed to update report for execution {execution_log_id}: {str(e)}"
            )
            # Don't raise - reporting errors should not affect execution
            return {
                "success": False,
                "error": str(e)
            }


# Convenience function for easy integration
def trigger_report_update(
    execution_log_id: str,
    user_id: str,
    db: Session
) -> dict:
    """
    Convenience function for triggering report updates.
    
    This can be called from execution endpoints after an execution completes.
    
    Example integration:
        # In your execution endpoint, after saving ExecutionLog:
        from reporting.event_hook import trigger_report_update
        
        # ... execution logic ...
        db.add(execution_log)
        db.commit()
        
        # Trigger report update (non-blocking observer)
        trigger_report_update(
            execution_log_id=str(execution_log.id),
            user_id=user_id,
            db=db
        )
    """
    return ReportingEventHook.trigger_report_update(
        execution_log_id, user_id, db
    )
