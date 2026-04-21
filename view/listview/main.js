const API = "http://localhost:8000/api";

let categories = [];

// INIT
window.onload = async () => {
  await loadCategories();
  await loadFeeds();
  await loadTasks();
};

// ---------------- FEEDS ----------------

async function loadFeeds() {
  const res = await fetch(`${API}/feeds`);
  const feeds = await res.json();

  const container = document.getElementById("feeds");
  container.innerHTML = "";

  feeds.forEach(f => {
    const div = document.createElement("div");
    div.innerHTML = `
      <b>${f.label}</b>
      <button onclick="syncFeed(${f.id})">Sync</button>
    `;
    container.appendChild(div);
  });
}

async function addFeed() {
  const url = document.getElementById("feed-url").value;
  const label = document.getElementById("feed-label").value;

  await fetch(`${API}/feeds`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ url, label })
  });

  loadFeeds();
}

async function syncFeed(id) {
  await fetch(`${API}/feeds/${id}/sync`, { method: "POST" });
  loadTasks();
}

// ---------------- CATEGORIES ----------------

async function loadCategories() {
  const res = await fetch(`${API}/categories`);
  categories = await res.json();
}

// ---------------- TASKS ----------------

function groupByDate(tasks) {
  const groups = {};

  tasks.forEach(task => {
    const date = new Date(task.start_time).toDateString();
    if (!groups[date]) groups[date] = [];
    groups[date].push(task);
  });

  return groups;
}

function statusColor(status) {
  return {
    none: "#9ca3af",
    to_do: "#f59e0b",
    in_progress: "#3b82f6",
    complete: "#10b981"
  }[status] || "#ccc";
}

async function loadTasks() {
  const res = await fetch(`${API}/tasks`);
  let tasks = await res.json();

  const sort = document.getElementById("sort").value;

  if (sort === "status") {
    tasks.sort((a,b) => a.status.localeCompare(b.status));
  } else if (sort === "category") {
    tasks.sort((a,b) => (a.categories[0]?.label || "").localeCompare(b.categories[0]?.label || ""));
  } else {
    tasks.sort((a,b) => new Date(a.start_time) - new Date(b.start_time));
  }

  const grouped = groupByDate(tasks);
  const container = document.getElementById("tasks");
  container.innerHTML = "";

  Object.keys(grouped).forEach(date => {
    const section = document.createElement("div");

    section.innerHTML = `<h3 style="margin-top:20px;">${date}</h3>`;

    grouped[date].forEach(task => {
      const div = document.createElement("div");
      div.className = "task";

      const catOptions = categories.map(c => 
        `<option value="${c.id}">${c.label}</option>`
      ).join("");

      div.style.borderLeft = `6px solid ${statusColor(task.status)}`;

      div.innerHTML = `
        <div style="display:flex; justify-content:space-between;">
          <div>
            <div class="task-title">${task.summary}</div>
            <div class="task-time">
              ${new Date(task.start_time).toLocaleTimeString()}
            </div>
          </div>

          <span class="status ${task.status}">
            ${task.status.replace("_"," ")}
          </span>
        </div>

        <div style="margin-top:10px;">
          <select onchange="updateStatus(${task.id}, this.value)">
            ${["none","to_do","in_progress","complete"]
              .map(s => `<option ${task.status===s?"selected":""}>${s}</option>`).join("")}
          </select>

          <select onchange="updateCategory(${task.id}, this.value)">
            <option value="">Category</option>
            ${catOptions}
          </select>
        </div>

        <div>
          ${task.categories.map(c =>
            `<span class="badge" style="background:${c.color}">${c.label}</span>`
          ).join("")}
        </div>
      `;

      section.appendChild(div);
    });

    container.appendChild(section);
  });
}
// ---------------- UPDATE ----------------

async function updateStatus(id, status) {
  await fetch(`${API}/tasks/${id}`, {
    method: "PUT",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ status })
  });

  loadTasks();
}

async function updateCategory(id, catId) {
  await fetch(`${API}/tasks/${id}`, {
    method: "PUT",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ cat_ids: catId ? [parseInt(catId)] : [] })
  });

  loadTasks();
}