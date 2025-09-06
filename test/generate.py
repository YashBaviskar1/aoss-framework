import random
import time
import uuid
from database.log import logger  # your StructuredLogger instance

agents = ["planner", "executor", "rag", "error-handler"]
statuses = ["success", "failure", "timeout", "retry"]

def generate_dummy_logs(n=50, sleep=0.2):
    for i in range(n):
        agent = random.choice(agents)
        status = random.choice(statuses)
        trace_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        logger.log(
            agent_role=agent,
            status=status,
            message=f"Dummy event {i+1}",
            payload={"iteration": i+1, "value": random.randint(1, 100)},
            rag_context_ids=[str(uuid.uuid4()) for _ in range(2)],
            task_id=task_id,
            trace_id=trace_id,
            duration_ms=random.randint(50, 1000),
        )

        print(f"[{i+1}] Logged event with trace_id={trace_id}, status={status}")
        time.sleep(sleep)


if __name__ == "__main__":
    generate_dummy_logs()
