function $(sel) {
  return document.querySelector(sel);
}

function setActivePageNav() {
  const path = (location.pathname.split("/").pop() || "").toLowerCase();
  document.querySelectorAll("[data-nav]").forEach((a) => {
    const href = (a.getAttribute("href") || "").toLowerCase();
    a.classList.toggle("active", href.endsWith(path));
  });
}

function requireAuth() {
  const token = window.EcoTrackAPI.getToken();
  if (!token) {
    location.href = "index.html";
  }
}

function logout() {
  window.EcoTrackAPI.setToken(null);
  location.href = "index.html";
}

async function login(email, password) {
  const data = await window.EcoTrackAPI.apiFetch("/auth/login", {
    method: "POST",
    body: { email, password },
  });
  window.EcoTrackAPI.setToken(data.access_token);
  location.href = "dashboard.html";
}

async function register(payload) {
  return await window.EcoTrackAPI.apiFetch("/auth/register", {
    method: "POST",
    body: payload,
  });
}

window.EcoTrackAuth = {
  requireAuth,
  logout,
  login,
  register,
  setActivePageNav,
};

