import { DEFAULT_PROJECT_ID } from "./projects";

const API = "/api";

function withProject(project, path) {
  const id = project || DEFAULT_PROJECT_ID;
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}project=${encodeURIComponent(id)}`;
}

function formatApiDetail(detail) {
  if (detail == null) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item.msg === "string") return item.msg;
        return JSON.stringify(item);
      })
      .join("; ");
  }
  if (typeof detail === "object" && typeof detail.message === "string") {
    return detail.message;
  }
  return JSON.stringify(detail);
}

async function request(url, options = {}) {
  const res = await fetch(`${API}${url}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatApiDetail(err.detail) || `Request failed (${res.status})`);
  }
  return res.json();
}

export const fetchProjects = () => request("/projects");
export const fetchTasks = (project = DEFAULT_PROJECT_ID) =>
  request(withProject(project, "/tasks"));
export const createTask = (project, payload) =>
  request(withProject(project, "/tasks"), {
    method: "POST",
    body: JSON.stringify(payload),
  });
export const updateProjectStart = (project, project_start) =>
  request(withProject(project, "/project-start"), {
    method: "PUT",
    body: JSON.stringify({ project_start }),
  });
export const updateTask = (project, id, payload) =>
  request(withProject(project, `/tasks/${id}`), {
    method: "PUT",
    body: JSON.stringify(payload),
  });
export const reorderTasks = (project, order) =>
  request(withProject(project, "/tasks/reorder"), {
    method: "PUT",
    body: JSON.stringify({ order }),
  });
export const deleteTask = (project, id) =>
  request(withProject(project, `/tasks/${id}`), { method: "DELETE" });
export const appendTaskLog = (project, id, message) =>
  request(withProject(project, `/tasks/${id}/log`), {
    method: "POST",
    body: JSON.stringify({ message }),
  });
export const logTaskDelay = (project, id, days, reason) =>
  request(withProject(project, `/tasks/${id}/delay`), {
    method: "POST",
    body: JSON.stringify({ days, reason }),
  });
export const shiftProject = (project, extra_days = 7) =>
  request(withProject(project, "/shift"), {
    method: "POST",
    body: JSON.stringify({ extra_days }),
  });
