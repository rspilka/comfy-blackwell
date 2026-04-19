# README - ComfyUI Monitor Service (English)

This document provides a technical overview of the **comfy-monitor** service.

## 1. Motivation
The **comfy-monitor** listens to ComfyUI's WebSocket stream to correlate hardware load with specific software events.

## 2. Function
The monitor uses `websocket-client` and `prometheus_client` to perform:
* **Real-time Event Tracking:** Connected to `/ws` for updates.
* **Node-Level Error Reporting:** Captures specific node failures.
* **Execution Timing:** Measures time spent on a prompt.
* **Metric Exposure:** Serves a Prometheus endpoint (port 9000).

## 3. Detailed Script Explanation

### A. Initialization & Connectivity
```python
self.host = os.environ.get("COMFY_HOST", "comfy-app:8188")
self.ws_url = f"ws://{self.host}/ws"
```

### B. Message Processing
The `on_message` function parses the JSON stream:
* **execution_start:** Maps Node IDs to Titles.
* **executing:** Updates status.
* **execution_error:** Increments error counters.

**Example Error Handling:**
```python
elif m_type == 'execution_error':
    node_name = self.active_jobs[p_id]["mapping"].get(node_id, node_type)
    NODE_ERRORS.labels(node_type=node_type).inc()
    print(f"❌ [ABBRUCH] Node: {node_name} | Error: {exception_msg}")
```

### C. Resilience & Error Handling
* **Auto-Reconnect:** Waits 5 seconds to reconnect.
* **Safe Parsing:** Wrapped in `try-except` blocks.

## 4. Exposed Metrics
* `comfy_active_jobs`
* `comfy_job_duration_seconds`
* `comfy_node_errors_total`
* `comfy_monitor_connected`
