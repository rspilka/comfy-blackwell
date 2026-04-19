import websocket
import json
import os
import time
import re
from datetime import datetime
from prometheus_client import start_http_server, Counter, Gauge, Histogram

# --- METRIKEN ---
MONITOR_ERRORS = Counter('comfy_monitor_errors_total', 'Interne Monitor-Fehler', ['type'])
NODE_ERRORS = Counter('comfy_node_errors_total', 'Abbrüche durch Node-Fehler', ['node_type'])
CONN_STATUS = Gauge('comfy_monitor_connected', 'Verbindungsstatus')
JOB_DURATION = Histogram('comfy_job_duration_seconds', 'Blackwell GPU Runtime', buckets=(1, 5, 10, 30, 60, 120, 300, 600))
ACTIVE_JOBS = Gauge('comfy_active_jobs', 'Laufende Jobs')

class BlackwellMonitor:
    def __init__(self):
        self.host = os.environ.get("COMFY_HOST", "comfy-app:8188")
        self.metrics_port = int(os.environ.get("METRICS_PORT", 9000))
        self.ws_url = f"ws://{self.host}/ws"
        self.active_jobs = {}

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            m_type, m_data = data.get('type'), data.get('data', {})

            # 1. Start: Mapping der Nodes für späteres Error-Reporting
            if m_type == 'execution_start':
                p_id = m_data.get('prompt_id')
                prompt = m_data.get('prompt', {})
                # Wir speichern das Mapping von ID zu Titel/Typ
                mapping = {nid: (n.get('_meta', {}).get('title') or n.get('class_type')) 
                           for nid, n in prompt.items()}
                
                self.active_jobs[p_id] = {
                    "start": time.time(),
                    "mapping": mapping
                }
                ACTIVE_JOBS.inc()
                print(f"🚀 [START] Job {p_id[:8]}")

            # 2. Fehlerfall: Hier wird es interessant
            elif m_type == 'execution_error':
                p_id = m_data.get('prompt_id')
                node_id = m_data.get('node_id')
                node_type = m_data.get('node_type')
                exception_msg = m_data.get('exception_message', 'Unbekannter Fehler')
                
                # Namen der Node aus unserem Mapping holen
                node_name = "Unbekannt"
                if p_id in self.active_jobs:
                    node_name = self.active_jobs[p_id]["mapping"].get(node_id, node_type)
                    ACTIVE_JOBS.dec()
                    del self.active_jobs[p_id]

                NODE_ERRORS.labels(node_type=node_type).inc()
                
                print(f"\n{'!'*60}")
                print(f"❌ [ABBRUCH] Job {p_id[:8]} gescheitert!")
                print(f"📍 Node: {node_name} (ID: {node_id})")
                print(f"📝 Fehler: {exception_msg}")
                print(f"{'!'*60}\n", flush=True)

            # 3. Normaler Fortschritt / Ende
            elif m_type == 'executing':
                p_id = m_data.get('prompt_id')
                node_id = m_data.get('node')

                if p_id in self.active_jobs:
                    if node_id is None: # Erfolgreich fertig
                        duration = time.time() - self.active_jobs[p_id]["start"]
                        JOB_DURATION.observe(duration)
                        ACTIVE_JOBS.dec()
                        print(f"✅ [FINISH] {p_id[:8]} in {round(duration, 2)}s")
                        del self.active_jobs[p_id]
                    else:
                        node_name = self.active_jobs[p_id]["mapping"].get(node_id, f"Node {node_id}")
                        print(f"📍 [AKTIV] -> {node_name}", flush=True)

        except Exception as e:
            MONITOR_ERRORS.labels(type='processing').inc()
            print(f"❌ Monitor Error: {e}")

    def run(self):
        start_http_server(self.metrics_port)
        while True:
            try:
                ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=lambda ws: CONN_STATUS.set(1),
                    on_message=self.on_message,
                    on_error=lambda ws, e: print(f"⚠️ WS-Error: {e}"),
                    on_close=lambda ws, s, m: CONN_STATUS.set(0)
                )
                ws.run_forever()
            except Exception:
                time.sleep(5)

if __name__ == "__main__":
    BlackwellMonitor().run()
