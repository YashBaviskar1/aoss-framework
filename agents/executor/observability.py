
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from prometheus_client import Counter, Histogram, start_http_server
import threading

# -----------------------------
# Service Identity
# -----------------------------
SERVICE_NAME = "aoss-executor-agent"

resource = Resource.create({
    "service.name": SERVICE_NAME,
    "service.version": "1.0.0",
    "deployment.environment": "production"
})

# -----------------------------
# Tracing (OpenTelemetry → Tempo)
# -----------------------------
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer("aoss.executor", "1.0.0")

otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

# -----------------------------
# Metrics (Prometheus)
# -----------------------------
EXECUTOR_PLANS_TOTAL = Counter(
    "executor_plans_total",
    "Total number of execution plans started"
)

EXECUTOR_STEPS_TOTAL = Counter(
    "executor_steps_total",
    "Total number of execution steps",
    ["status"]  # Labels: success, failure
)

EXECUTOR_COMMAND_DURATION = Histogram(
    "executor_command_duration_seconds",
    "Duration of command execution in seconds"
)

# Metrics server state
_metrics_server_started = False
_metrics_lock = threading.Lock()

def start_metrics_server(port: int = 8009):
    """
    Start Prometheus metrics HTTP endpoint.
    
    Thread-safe, idempotent - can be called multiple times safely.
    Only starts server once per process.
    
    Args:
        port: HTTP port for metrics endpoint (default: 8009)
    """
    global _metrics_server_started
    
    with _metrics_lock:
        if not _metrics_server_started:
            try:
                start_http_server(port)
                _metrics_server_started = True
                print(f"[Observability] Metrics server started on port {port}")
            except OSError as e:
                if "Address already in use" in str(e):
                    print(f"[Observability] Metrics server already running on port {port}")
                    _metrics_server_started = True
                else:
                    raise
