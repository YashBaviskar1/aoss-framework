import requests

BASE_URL = "http://127.0.0.1:8001"

def test_create_log():
    url = f"{BASE_URL}/logs/"
    payload = {
        "agent_role": "executor",
        "status": "success",
        "message": "Test log entry from client",
        "trace_id": "trace-123",
        "task_id": "task-456",
        "step_id": "step-1",
        "duration_ms": 150,
        "payload": {"info": "dummy"},
        "rag_context_ids": ["context1", "context2"]
    }
    r = requests.post(url, json=payload)
    print("POST /logs/ status:", r.status_code)
    print("Response:", r.json())
    return r.json()

def test_get_logs():
    url = f"{BASE_URL}/logs/"
    r = requests.get(url)
    print("\nGET /logs/ status:", r.status_code)
    print("Response:", r.json())

def test_metrics():
    url = f"{BASE_URL}/metrics"
    r = requests.get(url)
    print("\nGET /metrics status:", r.status_code)
    print("Prometheus snippet:\n", r.text[:300], "...\n")  # print only first 300 chars

if __name__ == "__main__":
    created = test_create_log()
    test_get_logs()
    test_metrics()


