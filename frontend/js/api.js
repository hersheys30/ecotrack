function apiBase() {
  return window.ECOTRACK_CONFIG?.API_BASE_URL || "http://127.0.0.1:8001";
}

function getToken() {
  return localStorage.getItem("ECOTRACK_TOKEN");
}

function setToken(token) {
  if (!token) localStorage.removeItem("ECOTRACK_TOKEN");
  else localStorage.setItem("ECOTRACK_TOKEN", token);
}

function authHeader() {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function apiFetch(path, { method = "GET", body, headers = {} } = {}) {
  const url = `${apiBase()}${path}`;
  const init = {
    method,
    headers: {
      ...headers,
      ...authHeader(),
    },
  };
  if (body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const res = await fetch(url, init);
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const msg = (data && data.detail) || (typeof data === "string" ? data : "Request failed");
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

window.EcoTrackAPI = {
  apiBase,
  getToken,
  setToken,
  apiFetch,
};

