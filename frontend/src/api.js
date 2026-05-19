const API = "/api";

async function request(url, options = {}) {
  const res = await fetch(`${API}${url}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const fetchTasks = () => request("/tasks");
export const createTask = (payload) =>
  request("/tasks", { method: "POST", body: JSON.stringify(payload) });
export const updateProjectStart = (project_start) =>
  request("/project-start", { method: "PUT", body: JSON.stringify({ project_start }) });
export const updateTask = (id, payload) =>
  request(`/tasks/${id}`, { method: "PUT", body: JSON.stringify(payload) });
export const deleteTask = (id) => request(`/tasks/${id}`, { method: "DELETE" });
export const appendTaskLog = (id, message) =>
  request(`/tasks/${id}/log`, { method: "POST", body: JSON.stringify({ message }) });
export const logTaskDelay = (id, hours, reason) =>
  request(`/tasks/${id}/delay`, {
    method: "POST",
    body: JSON.stringify({ hours, reason }),
  });
export const shiftProject = (extra_days = 7) =>
  request("/shift", { method: "POST", body: JSON.stringify({ extra_days }) });
