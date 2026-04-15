// Mostly AI Generated

const { useState, useEffect } = React;

function FullApiView() {
  // New state to track our filter toggles
  const [filters, setFilters] = useState({
    past: false,
    future: false,
    today: true,
  });
  const [data, setData] = useState({ tasks: [], categories: [], feeds: [] });
  const [showAdmin, setShowAdmin] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const API_BASE = window.location.origin + "/api";

  // Column definitions based on OpenAPI TaskStatus enum
  const columns = [
    {
      id: "none",
      label: "Unsorted",
      color: "bg-slate-500",
      shadow: "shadow-[0_0_8px_#64748b]",
      backgroundColor: "bg-slate-900/50",
    },
    {
      id: "to_do",
      label: "To Do",
      color: "bg-red-500",
      shadow: "shadow-[0_0_8px_#ef4444]",
      backgroundColor: "bg-red-500/30",
    },
    {
      id: "in_progress",
      label: "In Progress",
      color: "bg-yellow-500",
      shadow: "shadow-[0_0_8px_#eab308]",
      backgroundColor: "bg-yellow-500/30",
    },
    {
      id: "complete",
      label: "Complete",
      color: "bg-green-500",
      shadow: "shadow-[0_0_8px_#22c55e]",
      backgroundColor: "bg-green-500/30",
    },
  ];

  useEffect(() => {
    loadAll();
  }, [filters]);
  // Scan for icons after every render that changes the data or view state
  useEffect(() => {
    if (window.lucide) window.lucide.createIcons();
  }, [data, showAdmin, editingItem]);

  const loadAll = async () => {
    try {
      // 1. Build Query Parameters based on your openapi.json
      const params = new URLSearchParams();

      if (filters.today) {
        params.append("days_back", 0);
        params.append("days_ahead", 1);
      } else if (filters.past && filters.future) {
        params.append("days_back", 7);
        params.append("days_ahead", 7);
      } else {
        if (filters.past) {
          params.append("days_back", 7);
          params.append("days_ahead", 0);
        }
        if (filters.future) {
          params.append("days_ahead", 7);
          params.append("days_back", 0);
        }
      }
      //params.append('days_ahead', 0);
      //params.append('days_back', 0);

      // 2. Fetch with the dynamic query string
      const [t, c, f] = await Promise.all([
        fetch(`${API_BASE}/tasks?${params.toString()}`).then((r) => r.json()),
        fetch(`${API_BASE}/categories`).then((r) => r.json()),
        fetch(`${API_BASE}/feeds`).then((r) => r.json()),
      ]);

      setData({ tasks: t, categories: c, feeds: f });
    } catch (err) {
      console.error("API Load Failure:", err);
    }
  };

  // Helper to handle the mutual exclusivity of "Today"
  const toggleFilter = (type) => {
    setFilters((prev) => {
      if (type === "today") {
        return { past: false, future: false, today: true };
      }
      // If selecting past/future, unselect today
      return { ...prev, [type]: !prev[type], today: false };
    });
  };

  // --- TASK METHODS (PUT) ---
  const updateTask = async (id, payload) => {
    await fetch(`${API_BASE}/tasks/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    loadAll();
  };

  // --- FEED METHODS (POST, PUT, DELETE, SYNC) ---
  const handleFeedSubmit = async (e, id = null) => {
    e.preventDefault();
    const form = e.target;
    const payload = { label: form.label.value, url: form.url.value };
    const method = id ? "PUT" : "POST";
    const url = id ? `${API_BASE}/feeds/${id}` : `${API_BASE}/feeds`;

    await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setEditingItem(null);
    if (!id) form.reset();
    loadAll();
  };

  const deleteFeed = async (id) => {
    if (confirm("Delete this feed and all associated tasks?")) {
      await fetch(`${API_BASE}/feeds/${id}`, { method: "DELETE" });
      loadAll();
    }
  };

  const syncFeed = async (id) => {
    await fetch(`${API_BASE}/feeds/${id}/sync`, { method: "POST" });
    loadAll();
  };

  // --- CATEGORY METHODS (POST, PUT, DELETE) ---
  const handleCategorySubmit = async (e, id = null) => {
    e.preventDefault();
    const form = e.target;
    const payload = {
      label: form.label.value,
      color: form.color.value,
      value: parseInt(form.value.value || 0),
    };
    const method = id ? "PUT" : "POST";
    const url = id ? `${API_BASE}/categories/${id}` : `${API_BASE}/categories`;

    await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setEditingItem(null);
    if (!id) form.reset();
    loadAll();
  };

  const deleteCategory = async (id) => {
    if (confirm("Delete this category?")) {
      await fetch(`${API_BASE}/categories/${id}`, { method: "DELETE" });
      loadAll();
    }
  };

  // --- NATIVE DRAG AND DROP ---
  const onDragStart = (e, taskId) => e.dataTransfer.setData("taskId", taskId);
  const onDrop = (e, newStatus) => {
    const taskId = e.dataTransfer.getData("taskId");
    updateTask(taskId, { status: newStatus });
  };

  return (
    <div className="p-8 min-h-screen text-slate-200 bg-slate-950 font-sans">
      <header className="mb-10 border-b border-slate-800 pb-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-black tracking-tighter text-white underline decoration-blue-600">
            iCalPy+
          </h1>
          {/* Filter UI Elements */}
          <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 shadow-inner">
            <button
              onClick={() => toggleFilter("past")}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${filters.past ? "bg-slate-700 text-blue-400 shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
            >
              Last 7 Days
            </button>
            <button
              onClick={() => toggleFilter("today")}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${filters.today ? "bg-blue-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
            >
              Today Only
            </button>
            <button
              onClick={() => toggleFilter("future")}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${filters.future ? "bg-slate-700 text-blue-400 shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
            >
              Next 7 Days
            </button>
          </div>
          <div className="flex gap-3">
            <button
              onClick={loadAll}
              className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors"
            >
              <i data-lucide="refresh-cw" className="w-5 h-5"></i>
            </button>
            <button
              onClick={() => {
                setShowAdmin(!showAdmin);
                setEditingItem(null);
              }}
              className="flex items-center gap-2 bg-blue-600 px-5 py-2 rounded-lg hover:bg-blue-500 transition-all font-bold text-sm shadow-lg shadow-blue-500/20"
            >
              <i
                data-lucide={showAdmin ? "layout-dashboard" : "settings"}
                className="w-4 h-4"
              ></i>
              {showAdmin ? "Board" : "Settings"}
            </button>
          </div>
        </div>
      </header>

      {/* ... Rest of your Kanban Grid ... */}

      {!showAdmin ? (
        /* --- KANBAN BOARD (4 COLUMNS) --- */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {columns.map((col) => (
            <div
              key={col.id}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => onDrop(e, col.id)}
              className={`${col.backgroundColor} p-5 rounded-2xl border border-slate-800 min-h-[600px] flex flex-col shadow-inner`}
            >
              <h2 className="text-[14px] font-black uppercase tracking-[0.3em] text-slate-300 mb-6 flex items-center gap-2">
                <span
                  className={`w-1.5 h-1.5 rounded-full ${col.color} ${col.shadow}`}
                ></span>
                {col.label}
                <span className="ml-auto text-slate-00 px-2 py-0.5 rounded italic">
                  {data.tasks.filter((t) => t.status === col.id).length}
                </span>
              </h2>
              <div className="space-y-4 flex-1">
                {data.tasks
                  .filter((t) => t.status === col.id)
                  .map((task) => (
                    <div
                      key={task.id}
                      draggable
                      onDragStart={(e) => onDragStart(e, task.id)}
                      className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-xl cursor-grab active:cursor-grabbing hover:border-blue-500/50 transition-all group"
                    >
                      <p className="font-bold text-slate-100 group-hover:text-blue-400 transition-colors">
                        {task.summary}
                      </p>
                      <p className="text-[18px] text-slate-500 mt-2 font-mono uppercase">
                        {new Date(task.start_time).toLocaleDateString()}
                      </p>

                      <div className="flex flex-wrap gap-1.5 mt-4">
                        {task.categories.map((c) => (
                          <span
                            key={c.id}
                            className="text-[12px] px-2 py-0.5 rounded-md font-bold flex items-center gap-1"
                            style={{
                              color: c.color,
                              backgroundColor: c.color + "15",
                              border: `1px solid ${c.color}40`,
                            }}
                          >
                            {c.label}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                const newIds = task.categories
                                  .filter((cat) => cat.id !== c.id)
                                  .map((cat) => cat.id);
                                updateTask(task.id, { cat_ids: newIds });
                              }}
                              className="hover:text-white transition-colors ml-0.5 text-xs font-black"
                              title="Remove tag"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                        <select
                          value=""
                          onChange={(e) => {
                            const current = task.categories.map((x) => x.id);
                            const newId = parseInt(e.target.value);
                            if (newId && !current.includes(newId)) {
                              updateTask(task.id, {
                                cat_ids: [...current, newId],
                              });
                            }
                          }}
                          className="bg-slate-900 border-none text-[12px] rounded px-1 text-slate-500 cursor-pointer focus:ring-0 appearance-none"
                        >
                          <option value="" disabled>
                            + Tag
                          </option>
                          {data.categories.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* --- SETTINGS VIEW --- */
        <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* FEED MANAGER */}
          <section>
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-blue-500">
              <i data-lucide="rss"></i> iCal Sources
            </h2>
            <div className="grid gap-4">
              <form
                onSubmit={(e) =>
                  handleFeedSubmit(
                    e,
                    editingItem?.type === "feed" ? editingItem.id : null,
                  )
                }
                className="bg-slate-900 p-4 rounded-xl border border-blue-500/20 flex gap-3 shadow-md"
              >
                <input
                  name="label"
                  placeholder="Feed Label"
                  defaultValue={
                    editingItem?.type === "feed" ? editingItem.data.label : ""
                  }
                  required
                  className="bg-slate-800 rounded-lg p-2 text-sm flex-1 focus:ring-1 focus:ring-blue-500 outline-none"
                />
                <input
                  name="url"
                  placeholder="URL"
                  defaultValue={
                    editingItem?.type === "feed" ? editingItem.data.url : ""
                  }
                  required
                  className="bg-slate-800 rounded-lg p-2 text-sm flex-[2] focus:ring-1 focus:ring-blue-500 outline-none"
                />
                <button
                  type="submit"
                  className="bg-blue-600 px-6 rounded-lg font-bold text-sm hover:bg-blue-500 transition-colors"
                >
                  {editingItem?.type === "feed" ? "Update Feed" : "Add Feed"}
                </button>
                {editingItem?.type === "feed" && (
                  <button
                    type="button"
                    onClick={() => setEditingItem(null)}
                    className="text-slate-500 px-2 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                )}
              </form>
              <div className="grid grid-cols-1 gap-3">
                {data.feeds.map((f) => (
                  <div
                    key={f.id}
                    className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 flex gap-4 justify-between items-center group hover:bg-slate-900 transition-colors"
                  >
                    <div className="flex-1">
                      <p className="font-bold text-slate-100">{f.label}</p>
                      <p className="text-[12px] text-slate-500 font-mono truncate max-w-md">
                        {f.url}
                      </p>
                    </div>
                    <div>
                      <p className="text-[12px] font-bold text-slate-500 max-w-md">
                        Last synced at:
                      </p>
                      <p className="text-[14px] text-slate-500 max-w-md">
                        {new Date(f.synced_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex gap-2 items-center">
                      <button
                        onClick={() => syncFeed(f.id)}
                        className="p-2 text-slate-500 hover:text-green-500 transition-colors"
                        title="Sync Now"
                      >
                        <i data-lucide="refresh-cw" className="w-4 h-4"></i>
                      </button>
                      <button
                        onClick={() =>
                          setEditingItem({ type: "feed", id: f.id, data: f })
                        }
                        className="p-2 text-slate-500 hover:text-blue-500 transition-colors"
                        title="Edit"
                      >
                        <i data-lucide="edit-3" className="w-4 h-4"></i>
                      </button>
                      <button
                        onClick={() => deleteFeed(f.id)}
                        className="p-2 text-slate-500 hover:text-red-500 transition-colors"
                        title="Delete"
                      >
                        <i data-lucide="trash-2" className="w-4 h-4"></i>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* CATEGORY MANAGER */}
          <section>
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-blue-500">
              <i data-lucide="tag"></i> Category Manager
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
              <form
                onSubmit={(e) =>
                  handleCategorySubmit(
                    e,
                    editingItem?.type === "cat" ? editingItem.id : null,
                  )
                }
                className="lg:col-span-2 bg-slate-900 p-6 rounded-2xl border border-blue-500/20 space-y-4 h-fit shadow-md"
              >
                <h3 className="text-xs font-black uppercase text-slate-500 tracking-[0.2em]">
                  {editingItem?.type === "cat"
                    ? "Modify Tag"
                    : "Create New Tag"}
                </h3>
                <input
                  name="label"
                  placeholder="Tag Label"
                  defaultValue={
                    editingItem?.type === "cat" ? editingItem.data.label : ""
                  }
                  required
                  className="w-full bg-slate-800 rounded-lg p-3 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
                />
                <div className="flex gap-4">
                  <div className="flex flex-col gap-1 flex-1">
                    <label className="text-[9px] uppercase font-bold text-slate-500">
                      Color
                    </label>
                    <input
                      name="color"
                      type="color"
                      key={editingItem?.id || "new"}
                      defaultValue={
                        editingItem?.type === "cat"
                          ? editingItem.data.color
                          : "#3b82f6"
                      }
                      className="h-12 w-full bg-slate-800 rounded border-none cursor-pointer p-1"
                    />
                  </div>
                  <div className="flex flex-col gap-1 flex-1">
                    <label className="text-[9px] uppercase font-bold text-slate-500">
                      Weight
                    </label>
                    <input
                      name="value"
                      type="number"
                      placeholder="0"
                      key={editingItem?.id || "new"}
                      defaultValue={
                        editingItem?.type === "cat" ? editingItem.data.value : 0
                      }
                      className="w-full bg-slate-800 rounded-lg p-3 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
                    />
                  </div>
                </div>
                <div className="flex gap-2 pt-2">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 py-3 rounded-lg font-bold text-sm hover:bg-blue-500 transition-all shadow-lg shadow-blue-500/20 active:scale-95"
                  >
                    {editingItem?.type === "cat"
                      ? "Save Changes"
                      : "Create Tag"}
                  </button>
                  {editingItem?.type === "cat" && (
                    <button
                      type="button"
                      onClick={() => setEditingItem(null)}
                      className="bg-slate-800 px-6 rounded-lg text-sm hover:bg-slate-700 transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </form>
              <div className="lg:col-span-3 space-y-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                {data.categories.map((c) => (
                  <div
                    key={c.id}
                    className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 flex justify-between items-center group hover:bg-slate-900 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor: c.color,
                          boxShadow: `0 0 10px ${c.color}66`,
                        }}
                      ></span>
                      <div>
                        <span className="font-bold text-slate-200 block">
                          {c.label}
                        </span>
                        <span className="text-[9px] text-slate-600 font-mono tracking-tighter">
                          VALUE:{c.value} // ID:{c.id}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                      <button
                        onClick={() =>
                          setEditingItem({ type: "cat", id: c.id, data: c })
                        }
                        className="p-2 text-slate-500 hover:text-blue-500 transition-colors"
                      >
                        <i data-lucide="edit-3" className="w-4 h-4"></i>
                      </button>
                      <button
                        onClick={() => deleteCategory(c.id)}
                        className="p-2 text-slate-500 hover:text-red-500 transition-colors"
                      >
                        <i data-lucide="trash-2" className="w-4 h-4"></i>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<FullApiView />);
