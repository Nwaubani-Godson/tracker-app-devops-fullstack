from fastapi import FastAPI, Request, HTTPException  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import Response, JSONResponse  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import Dict, List
from uuid import uuid4
import logging, time, uuid, os, json

# Prometheus
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
from prometheus_fastapi_instrumentator import Instrumentator  # type: ignore

# ---------- Structured JSON logging ----------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        obj = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # include request_id if attached
        if hasattr(record, "request_id"):
            obj["request_id"] = record.request_id
        # include any extra dict field (safe)
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            obj.update(extra)
        return json.dumps(obj, ensure_ascii=False)

# logger config
logger = logging.getLogger("prom_tasks_tracker")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
if not logger.handlers:
    sh = logging.StreamHandler()
    sh.setFormatter(JsonFormatter())
    logger.addHandler(sh)

# also write to a rotating file for local persistence; fluent bit will read this file
from logging.handlers import RotatingFileHandler

log_file = os.getenv("APP_LOG_PATH", "/var/log/prom_tasks/app.log")

# Ensure the directory exists before creating the handler
log_dir = os.path.dirname(log_file)
os.makedirs(log_dir, exist_ok=True)

fh = RotatingFileHandler(log_file, maxBytes=10_000_000, backupCount=5)
fh.setFormatter(JsonFormatter())
logger.addHandler(fh)

# ---------- FastAPI app ----------
app = FastAPI(title="Prom Tasks Tracker API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Request ID middleware (correlate logs) ----------
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    except Exception as e:
        logger.exception("Unhandled exception", extra={"request_id": req_id})
        raise

# ---------- Business model ----------
class Task(BaseModel):
    id: str = None
    title: str
    completed: bool = False

tasks: Dict[str, Dict] = {}

# ---------- Prometheus metrics (in-app) ----------
REQUEST_INPROGRESS = Gauge("api_requests_in_progress", "Requests currently in progress")
REQUEST_COUNT = Counter("api_requests_total", "Total API requests", ["method", "endpoint", "status"])
TASKS_CREATED = Counter("tasks_created_total", "Number of tasks created")
TASKS_COMPLETED = Counter("tasks_completed_total", "Number of tasks completed")
ACTIVE_TASKS = Gauge("active_tasks", "Number of tasks currently stored")
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "Latency of API requests", buckets=[0.005,0.01,0.025,0.05,0.1,0.25,0.5,1,2.5,5])

# ---------- metrics endpoint (exposed by the app) ----------
@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get("/healthz")
def health():
    return JSONResponse({"status": "ok"})

# ---------- Instrumentation: auto-instrument HTTP metrics ----------
Instrumentator().instrument(app).expose(app)

# ---------- API endpoints ----------
@app.get("/tasks", response_model=List[Task])
def list_tasks(request: Request):
    start = time.time()
    REQUEST_INPROGRESS.inc()
    try:
        res = list(tasks.values())
        logger.info("list_tasks", extra={"request_id": request.state.request_id, "extra": {"count": len(res)}})
        REQUEST_COUNT.labels(method="GET", endpoint="/tasks", status="200").inc()
        return res
    except Exception:
        REQUEST_COUNT.labels(method="GET", endpoint="/tasks", status="500").inc()
        logger.exception("Error in list_tasks", extra={"request_id": request.state.request_id})
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        latency = time.time() - start
        REQUEST_LATENCY.observe(latency)
        REQUEST_INPROGRESS.dec()

@app.post("/tasks", response_model=Task, status_code=201)
def add_task(task: Task, request: Request):
    start = time.time()
    REQUEST_INPROGRESS.inc()
    try:
        task.id = str(uuid4())
        tasks[task.id] = task.dict()
        TASKS_CREATED.inc()
        ACTIVE_TASKS.set(len(tasks))
        REQUEST_COUNT.labels(method="POST", endpoint="/tasks", status="201").inc()
        logger.info("task_created", extra={"request_id": request.state.request_id, "extra": {"task_id": task.id}})
        return task
    except Exception:
        REQUEST_COUNT.labels(method="POST", endpoint="/tasks", status="500").inc()
        logger.exception("Error in add_task", extra={"request_id": request.state.request_id})
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        REQUEST_INPROGRESS.dec()
        REQUEST_LATENCY.observe(time.time() - start)

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, updated_task: Task, request: Request):
    start = time.time()
    REQUEST_INPROGRESS.inc()
    try:
        if task_id not in tasks:
            REQUEST_COUNT.labels(method="PUT", endpoint="/tasks/{task_id}", status="404").inc()
            raise HTTPException(status_code=404, detail="Task not found")
        updated_task.id = task_id
        tasks[task_id] = updated_task.dict()
        if updated_task.completed:
            TASKS_COMPLETED.inc()
        ACTIVE_TASKS.set(len(tasks))
        REQUEST_COUNT.labels(method="PUT", endpoint="/tasks/{task_id}", status="200").inc()
        logger.info("task_updated", extra={"request_id": request.state.request_id, "extra": {"task_id": task_id}})
        return updated_task
    except HTTPException:
        raise
    except Exception:
        REQUEST_COUNT.labels(method="PUT", endpoint="/tasks/{task_id}", status="500").inc()
        logger.exception("Error in update_task", extra={"request_id": request.state.request_id})
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        REQUEST_INPROGRESS.dec()
        REQUEST_LATENCY.observe(time.time() - start)

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, request: Request):
    start = time.time()
    REQUEST_INPROGRESS.inc()
    try:
        if task_id not in tasks:
            REQUEST_COUNT.labels(method="DELETE", endpoint="/tasks/{task_id}", status="404").inc()
            raise HTTPException(status_code=404, detail="Task not found")
        was_completed = tasks[task_id].get("completed", False)
        del tasks[task_id]
        ACTIVE_TASKS.set(len(tasks))
        REQUEST_COUNT.labels(method="DELETE", endpoint="/tasks/{task_id}", status="200").inc()
        logger.info("task_deleted", extra={"request_id": request.state.request_id, "extra": {"task_id": task_id}})
        return {"message": "Task deleted"}
    except HTTPException:
        raise
    except Exception:
        REQUEST_COUNT.labels(method="DELETE", endpoint="/tasks/{task_id}", status="500").inc()
        logger.exception("Error in delete_task", extra={"request_id": request.state.request_id})
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        REQUEST_INPROGRESS.dec()
        REQUEST_LATENCY.observe(time.time() - start)
