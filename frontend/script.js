//const API = "http://backend:8000/tasks"; // uncomment for local dev test not in use.
//const API = "http://localhost:8000/tasks"; // uncomment for local dev test
const API = "http://107.23.92.88:8000/tasks";


async function loadTasks() {
  const res = await fetch(API);
  const tasks = await res.json();
  const list = document.getElementById("taskList");
  list.innerHTML = "";

  tasks.forEach(task => {
    const li = document.createElement("li");

    // Left section: task title
    const taskText = document.createElement("span");
    taskText.innerText = task.title;
    if (task.completed) {
      taskText.classList.add("completed");
    }

    // Right section
    const rightSection = document.createElement("div");
    rightSection.style.display = "flex";
    rightSection.style.alignItems = "center";

    // "Completed" label if task is completed
    if (task.completed) {
      const status = document.createElement("span");
      status.innerText = "Completed";
      status.className = "completed";
      status.style.marginRight = "10px";
      rightSection.appendChild(status);
    }

    // Dropdown menu
    const dropdown = document.createElement("select");
    dropdown.className = "dropdown";
    dropdown.innerHTML = `
      <option selected disabled>Action</option>
      <option value="complete">Mark as Completed</option>
      <option value="delete">Delete</option>
    `;
    dropdown.onchange = () => handleAction(task.id, dropdown.value);
    rightSection.appendChild(dropdown);

    li.appendChild(taskText);
    li.appendChild(rightSection);
    list.appendChild(li);
  });
}

async function addTask() {
  const input = document.getElementById("taskInput");
  const title = input.value.trim();
  if (!title) return;

  await fetch(API, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });

  input.value = "";
  loadTasks();
}

async function handleAction(taskId, action) {
  if (action === "delete") {
    await fetch(`${API}/${taskId}`, { method: "DELETE" });
  } else if (action === "complete") {
    // Get the task
    const res = await fetch(API);
    const tasks = await res.json();
    const task = tasks.find(t => t.id === taskId);
    if (!task || task.completed) return;

    task.completed = true;
    await fetch(`${API}/${taskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(task),
    });
  }
  loadTasks();
}

window.onload = loadTasks;
