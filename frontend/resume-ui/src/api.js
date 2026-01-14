const API_BASE =
  import.meta.env.VITE_API_BASE ||
  "https://resume-ai-production-d7e7.up.railway.app";

/**
 * Low-level helper
 */
async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }

  return res.json();
}

/* ============================
   Resume
============================ */

export function fetchResume() {
  return request("/api/resume");
}

export function saveResume(resume) {
  return request("/api/resume", {
    method: "POST",
    body: JSON.stringify(resume)
  });
}

export function updateBullet(expIndex, bulletIndex, text) {
  return request("/api/resume/bullet", {
    method: "POST",
    body: JSON.stringify({
      exp_index: expIndex,
      bullet_index: bulletIndex,
      text
    })
  });
}

/* ============================
   Variants
============================ */

export function listVariants() {
  return request("/api/variants");
}

export function createVariant(name) {
  return request("/api/variant", {
    method: "POST",
    body: JSON.stringify({ name })
  });
}

export function activateVariant(name) {
  return request("/api/variant/activate", {
    method: "POST",
    body: JSON.stringify({ name })
  });
}

/* ============================
   Scoring & Decisions
============================ */

export function scoreVariant(job) {
  return request("/api/variant/score", {
    method: "POST",
    body: JSON.stringify({ job })
  });
}

export function bulletImpact(job) {
  return request("/api/variant/bullet-impact", {
    method: "POST",
    body: JSON.stringify({ job })
  });
}

export function bulletDecisions(job) {
  return request("/api/variant/bullet-decisions", {
    method: "POST",
    body: JSON.stringify({ job })
  });
}

export function applyRemovals(job, confirm = false, dryRun = false) {
  return request("/api/variant/apply-removals", {
    method: "POST",
    body: JSON.stringify({
      job,
      confirm,
      dry_run: dryRun
    })
  });
}

/* ============================
   Metrics
============================ */

export function fetchMetrics() {
  return request("/api/metrics");
}

export function fetchLatestMetrics() {
  return request("/api/metrics/latest");
}

export function fetchAggregatedMetrics() {
  return request("/api/metrics/aggregate");
}