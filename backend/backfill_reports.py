"""
Backfill Governance Reports for Existing Execution Logs

This script generates governance reports for all existing execution logs
that don't have associated reports yet.
"""

from database import SessionLocal
from models import ExecutionLog, GovernanceReport
from reporting.event_hook import trigger_report_update
from sqlalchemy import func

def backfill_reports():
    """Generate reports for all existing execution logs."""
    db = SessionLocal()
    
    try:
        # Get all execution logs
        logs = db.query(ExecutionLog).order_by(ExecutionLog.created_at.asc()).all()
        
        print(f"Found {len(logs)} execution logs in database")
        
        if len(logs) == 0:
            print("No execution logs found. Execute some commands first.")
            return
        
        # Process each log
        generated_count = 0
        skipped_count = 0
        
        for log in logs:
            try:
                # Check if report already exists for this execution
                existing_report = db.query(GovernanceReport).filter(
                    GovernanceReport.user_id == log.user_id
                ).first()
                
                if existing_report:
                    # Check if this execution is already in the report
                    executions = existing_report.executions or []
                    if any(exec.get('execution_log_id') == str(log.id) for exec in executions):
                        print(f"  Skipping log {log.id} - already in report")
                        skipped_count += 1
                        continue
                
                # Generate report for this execution
                print(f"  Generating report for execution {log.id}...")
                result = trigger_report_update(
                    execution_log_id=str(log.id),
                    user_id=log.user_id,
                    db=db
                )
                
                if result.get('success'):
                    generated_count += 1
                    print(f"    ✓ Report generated successfully")
                else:
                    print(f"    ✗ Failed: {result.get('error')}")
                    
            except Exception as e:
                print(f"  Error processing log {log.id}: {e}")
                continue
        
        print(f"\n✓ Backfill complete!")
        print(f"  Generated: {generated_count} reports")
        print(f"  Skipped: {skipped_count} (already existed)")
        
    except Exception as e:
        print(f"Error during backfill: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting Governance Reports Backfill...\n")
    backfill_reports()
