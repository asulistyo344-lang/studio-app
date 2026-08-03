const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8006/studio";

async function request(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || `Request failed with status ${response.status}`);
  }

  return data;
}

export function getStyles() {
  return request("/styles");
}

export function getHealth() {
  return request("/health");
}

export function generateImages({ niche, style, images, userPrompt }) {
  return request("/generate-images", {
    method: "POST",
    body: JSON.stringify({
      niche,
      style,
      images,
      user_prompt: userPrompt || undefined,
      n_variants: 3,
    }),
  });
}

export function generate3D({ images, userPrompt, provider }) {
  return request("/generate-3d", {
    method: "POST",
    body: JSON.stringify({
      images,
      user_prompt: userPrompt || undefined,
      provider: provider || "byteplus_hyper3d",
    }),
  });
}

export function animate3D({ modelUrl, motionType }) {
  return request("/animate-3d", {
    method: "POST",
    body: JSON.stringify({
      model_url: modelUrl,
      motion_type: motionType,
    }),
  });
}

export function register({ email, password }) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function login({ email, password }) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function logout() {
  return request("/auth/logout", { method: "POST" });
}

export function getMe() {
  return request("/auth/me");
}

export function verifyEmail(token) {
  return request("/auth/verify-email", { method: "POST", body: JSON.stringify({ token }) });
}

export function forgotPassword(email) {
  return request("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }) });
}

export function resetPassword(token, newPassword) {
  return request("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export function getJobStatus(jobId) {
  return request(`/jobs/${jobId}`);
}

export function listJobs() {
  return request("/jobs");
}

export function getAccount() {
  return request("/me/account");
}

export function upgradeSubscription(plan) {
  return request("/me/subscription/upgrade", { method: "POST", body: JSON.stringify({ plan }) });
}

export function listProjects() {
  return request("/projects");
}

export function createProject(name) {
  return request("/projects", { method: "POST", body: JSON.stringify({ name }) });
}

export function deleteProject(id) {
  return request(`/projects/${id}`, { method: "DELETE" });
}

export function adminListUsers({ limit = 50, offset = 0, q = "" } = {}) {
  const query = q ? `&q=${encodeURIComponent(q)}` : "";
  return request(`/admin/users?limit=${limit}&offset=${offset}${query}`);
}

export function adminUpdateUser(userId, payload) {
  return request(`/admin/users/${userId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function adminListJobs({ limit = 50, offset = 0 } = {}) {
  return request(`/admin/jobs?limit=${limit}&offset=${offset}`);
}

export function adminRetryJob(jobId) {
  return request(`/admin/jobs/${jobId}/retry`, { method: "POST" });
}

export function adminGetStats() {
  return request("/admin/stats");
}

export function adminListAuditLogs({ limit = 50, offset = 0 } = {}) {
  return request(`/admin/audit-logs?limit=${limit}&offset=${offset}`);
}

export function listNotifications() {
  return request("/me/notifications");
}

export function markNotificationRead(id) {
  return request(`/me/notifications/${id}/read`, { method: "PATCH" });
}

export function markAllNotificationsRead() {
  return request("/me/notifications/read-all", { method: "PATCH" });
}

// Generation endpoints now return immediately with a pending job (async job
// queue, not a synchronous result) — poll job status until it settles.
export function pollJob(jobId, { intervalMs = 4000, onTick } = {}) {
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const job = await getJobStatus(jobId);
        if (onTick) onTick(job);

        if (job.status === "completed") {
          resolve(job);
        } else if (job.status === "failed") {
          reject(new Error(job.error_message || "Generation failed. Please retry."));
        } else {
          setTimeout(tick, intervalMs);
        }
      } catch (err) {
        reject(err);
      }
    };
    tick();
  });
}
