"""
Prometheus Metrics for AOSS Execution System

This module defines and manages Prometheus metrics for the AOSS backend.
Metrics track execution lifecycle events without modifying core logic.

CRITICAL: This is READ-ONLY observability. Does NOT affect execution behavior.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Dict


# ============================================================================
# METRIC DEFINITIONS
# ============================================================================

# Counter: Total number of executions started
executions_total = Counter(
    'aoss_executions_total',
    'Total number of AOSS executions started',
    ['agent_type', 'server_tag']
)

# Counter: Total number of executions completed
executions_completed = Counter(
    'aoss_executions_completed',
    'Total number of AOSS executions completed',
    ['agent_type', 'server_tag', 'status']
)

# Counter: Total number of execution steps
execution_steps_total = Counter(
    'aoss_execution_steps_total',
    'Total number of execution steps',
    ['agent_type', 'status']
)

# Counter: Execution errors by type
execution_errors_total = Counter(
    'aoss_execution_errors_total',
    'Total number of execution errors',
    ['error_type', 'agent_type']
)

# Histogram: Execution duration in seconds
execution_duration_seconds = Histogram(
    'aoss_execution_duration_seconds',
    'Duration of AOSS executions in seconds',
    ['agent_type', 'status'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)
)

# Gauge: Currently active executions
active_executions = Gauge(
    'aoss_active_executions',
    'Number of currently running executions',
    ['agent_type']
)

# Counter: Self-healing attempts
self_healing_attempts = Counter(
    'aoss_self_healing_attempts',
    'Total number of self-healing recovery attempts',
    ['agent_type', 'success']
)

# Counter: API requests
api_requests_total = Counter(
    'aoss_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

# Counter: Database operations
db_operations_total = Counter(
    'aoss_db_operations_total',
    'Total number of database operations',
    ['operation', 'table']
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def record_execution_start(agent_type: str = "general", server_tag: str = "unknown"):
    """
    Record the start of an execution.
    
    Call this when an execution begins.
    """
    executions_total.labels(agent_type=agent_type, server_tag=server_tag).inc()
    active_executions.labels(agent_type=agent_type).inc()


def record_execution_complete(
    agent_type: str = "general",
    server_tag: str = "unknown",
    status: str = "Success",
    duration_seconds: float = 0.0
):
    """
    Record the completion of an execution.
    
    Call this when an execution finishes (success or failure).
    """
    executions_completed.labels(
        agent_type=agent_type,
        server_tag=server_tag,
        status=status
    ).inc()
    
    active_executions.labels(agent_type=agent_type).dec()
    
    if duration_seconds > 0:
        execution_duration_seconds.labels(
            agent_type=agent_type,
            status=status
        ).observe(duration_seconds)


def record_execution_step(agent_type: str = "general", status: str = "Success"):
    """
    Record the completion of a single execution step.
    
    Call this after each step completes.
    """
    execution_steps_total.labels(agent_type=agent_type, status=status).inc()


def record_execution_error(error_type: str, agent_type: str = "general"):
    """
    Record an execution error.
    
    Call this when an error occurs during execution.
    """
    execution_errors_total.labels(error_type=error_type, agent_type=agent_type).inc()


def record_self_healing(agent_type: str = "general", success: bool = True):
    """
    Record a self-healing attempt.
    
    Call this when the system attempts to recover from a failure.
    """
    success_str = "true" if success else "false"
    self_healing_attempts.labels(agent_type=agent_type, success=success_str).inc()


def record_api_request(method: str, endpoint: str, status_code: int):
    """
    Record an API request.
    
    Call this from middleware or endpoint handlers.
    """
    api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code)
    ).inc()


def record_db_operation(operation: str, table: str):
    """
    Record a database operation.
    
    Call this when performing DB operations (optional).
    """
    db_operations_total.labels(operation=operation, table=table).inc()


# ============================================================================
# METRICS ENDPOINT
# ============================================================================

def get_metrics() -> Response:
    """
    Generate Prometheus metrics in text format.
    
    This function is called by the /metrics endpoint.
    
    Returns:
        Response with Prometheus text format metrics
    """
    metrics_output = generate_latest()
    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_metrics_summary() -> Dict[str, int]:
    """
    Get a summary of current metrics (for debugging).
    
    Returns:
        Dictionary with metric names and values
    """
    # This is a simplified summary - actual values are tracked by prometheus_client
    return {
        "note": "Use /metrics endpoint for full Prometheus output"
    }
