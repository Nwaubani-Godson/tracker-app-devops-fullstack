from fastapi.testclient import TestClient # type: ignore
from backend.main import app  
import sys
print(sys.path)


client = TestClient(app)

def test_create_get_update_delete_tasks():
    # Create a task
    response = client.post("/tasks", json={"title": "Test Task"})
    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Test Task"
    assert task["completed"] is False
    task_id = task["id"]

    # Get tasks and verify the new task is in the list
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert any(t["id"] == task_id for t in tasks)

    # Update the task to mark it completed
    updated_data = {"title": "Test Task", "completed": True, "id": task_id}
    response = client.put(f"/tasks/{task_id}", json=updated_data)
    assert response.status_code == 200
    updated_task = response.json()
    assert updated_task["completed"] is True

    # Delete the task
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Task deleted"}

    # Verify task is deleted by trying to get the list again
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert all(t["id"] != task_id for t in tasks)
