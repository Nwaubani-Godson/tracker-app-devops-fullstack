from fastapi import FastAPI, HTTPException, Request  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import List
from uuid import uuid4
import logging
from logging.handlers import RotatingFileHandler
import time
from prometheus_client import start_http_server, Counter, Gauge, Summary, Histogram  # type: ignore
import threading

# ------------------ Logging Configuration ------------------ #
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Log to file with rotation
file_handler = RotatingFileHandler("app.log", maxBytes=1_000_000, backupCount=5)
file_handler.setFormatter(log_formatter)

# Log to console
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Logger setup
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False  # Avoid duplicate logs

# ------------------ Prometheus Metrics ------------------ #
REQUEST_COUNT = Counter("api_requests_count_total", "Total number of API requests", ["api_name", "endpoint"])
TASKS_CREATED = Counter("tasks_created_count_total", "Number of tasks created", ["api_name", "endpoint"])
REQUEST_INPROGRESS = Gauge("api_requests_in_progress", "Number of API requests in progress")
ACTIVE_TASKS = Gauge("active_tasks", "Current number of active tasks in memory")
REQUEST_LAST_SERVED = Gauge("api_requests_last_served", "Timestamp of the last served API request"  )
REQUEST_RESPOND_TIME_SUMMARY = Summary("api_response_latency_seconds", "Response latency in seconds")
REQUEST_RESPOND_TIME_HISTOGRAM = Histogram("api_response_latency_histogram_seconds", "response latency histogram in seconds")

app = FastAPI()

# ------------------ Prometheus Metrics Server ------------------ #
def start_metrics_server():
    start_http_server(8001)
    logger.info("Prometheus metrics server started on port 8001")

threading.Thread(target=start_metrics_server).start()

# ------------------ Request Logging Middleware ------------------ #
@app.middleware("http")
async def log_request_data(request: Request, call_next):
    try:
        body = await request.body()
        logger.info(f"Request path: {request.url.path} | Method: {request.method} | Payload: {body.decode('utf-8')}")
    except Exception as e:
        logger.error(f"Error logging request data: {e}")
    response = await call_next(request)
    REQUEST_LAST_SERVED.set(time.time())
    return response

# ------------------ CORS ------------------ #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ In-memory Task Store ------------------ #
tasks = {}

class Task(BaseModel):
    id: str = None
    title: str
    completed: bool = False

# ------------------ API Endpoints ------------------ #

@app.get("/tasks", response_model=List[Task])
def list_tasks():
    start_time = time.time()
    try:
        REQUEST_COUNT.labels(api_name="prom_tasks_tracker_api", endpoint="/tasks").inc()
        REQUEST_INPROGRESS.inc()
        # time.sleep(10)  # Simulate delay, you can uncomment to test delay and get the request_inprogress metric
        response = list(tasks.values())
        return response
    except Exception as e:
        logger.error(f"Error in GET /tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        REQUEST_INPROGRESS.dec()
        time_taken = time.time() - start_time
        REQUEST_RESPOND_TIME_SUMMARY.observe(time_taken)
        REQUEST_RESPOND_TIME_HISTOGRAM.observe(time_taken)


@app.post("/tasks", response_model=Task)
def add_task(task: Task):
    start_time = time.time()
    try:
        task.id = str(uuid4())
        tasks[task.id] = task
        TASKS_CREATED.labels(api_name="prom_tasks_tracker_api", endpoint="/tasks").inc()
        ACTIVE_TASKS.inc()
        return task
    except Exception as e:
        logger.error(f"Error in POST /tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        time_taken = time.time() - start_time
        REQUEST_RESPOND_TIME_SUMMARY.observe(time_taken)
        REQUEST_RESPOND_TIME_HISTOGRAM.observe(time_taken)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, updated_task: Task):
    start_time = time.time()
    try:
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        updated_task.id = task_id
        tasks[task_id] = updated_task
        return updated_task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in PUT /tasks/{task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        time_taken = time.time() - start_time
        REQUEST_RESPOND_TIME_SUMMARY.observe(time_taken)
        REQUEST_RESPOND_TIME_HISTOGRAM.observe(time_taken)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    start_time = time.time()
    try:
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        del tasks[task_id]
        ACTIVE_TASKS.dec()
        return {"message": "Task deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in DELETE /tasks/{task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        time_taken = time.time() - start_time
        REQUEST_RESPOND_TIME_SUMMARY.observe(time_taken)
        REQUEST_RESPOND_TIME_HISTOGRAM.observe(time_taken)
