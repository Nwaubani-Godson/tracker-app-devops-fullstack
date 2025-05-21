from fastapi import FastAPI, HTTPException  # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import List
from uuid import uuid4

app = FastAPI()

# Enable CORS so frontend on another origin can access the API
app.add_middleware(
    CORSMiddleware,
     allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task storage
tasks = {}

class Task(BaseModel):
    id: str = None
    title: str
    completed: bool = False

@app.get("/tasks", response_model=List[Task])
def list_tasks():
    return list(tasks.values())

@app.post("/tasks", response_model=Task)
def add_task(task: Task):
    task.id = str(uuid4())
    tasks[task.id] = task
    return task

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, updated_task: Task):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    updated_task.id = task_id
    tasks[task_id] = updated_task
    return updated_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return {"message": "Task deleted"}
