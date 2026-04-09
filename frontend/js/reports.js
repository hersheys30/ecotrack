function el(id) {
  return document.getElementById(id);
}

function setStatus(kind, msg) {
  const box = el("reportsStatus");
  if (!msg) {
    box.style.display = "none";
    return;
  }
  box.style.display = "block";
  box.className = `notice ${kind === "err" ? "err" : kind === "ok" ? "ok" : ""}`;
  box.innerHTML = msg;
}

function qs(params) {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    u.set(k, String(v));
  }
  const s = u.toString();
  return s ? `?${s}` : "";
}

async function loadLogs() {
  setStatus("", "");
  const scope = el("scope").value ? Number(el("scope").value) : null;
  const start = el("start").value || null;
  const end = el("end").value || null;
  const limit = 50;

  try {
    const rows = await window.EcoTrackAPI.apiFetch(`/activity-logs${qs({ scope, start, end, limit })}`);
    const tbody = el("logsBody");
    tbody.innerHTML = "";
    for (const r of rows) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="mono">#${r.id}</td>
        <td class="mono">${r.date}</td>
        <td>Scope ${r.scope}</td>
        <td>${r.activity_type}</td>
        <td class="mono">${Number(r.quantity).toFixed(2)} ${r.unit}</td>
        <td class="mono">${r.calculated_co2e == null ? "-" : Number(r.calculated_co2e).toFixed(2)}</td>
      `;
      tbody.appendChild(tr);
    }
    setStatus("ok", `<b>Loaded.</b> Showing the latest ${rows.length} activity logs.`);
  } catch (e) {
    setStatus("err", `<b>Couldn’t load logs.</b> ${e.message || e}`);
  }
}

async function exportCSV() {
  setStatus("", "");
  const scope = el("scope").value ? Number(el("scope").value) : null;
  const start = el("start").value || null;
  const end = el("end").value || null;
  const activity_type = el("activity_type").value || null;
  const token = window.EcoTrackAPI.getToken();
  const url = `${window.EcoTrackAPI.apiBase()}/reports/export${qs({ format: "csv", scope, start, end, activity_type })}`;

  try {
    const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!res.ok) throw new Error(`Export failed (${res.status})`);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "ecotrack_report.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setStatus("ok", `<b>Exported.</b> CSV download started.`);
  } catch (e) {
    setStatus("err", `<b>Couldn’t export CSV.</b> ${e.message || e}`);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  window.EcoTrackAuth.requireAuth();
  window.EcoTrackAuth.setActivePageNav();

  el("btnLogout").addEventListener("click", window.EcoTrackAuth.logout);
  el("btnApply").addEventListener("click", loadLogs);
  el("btnExport").addEventListener("click", exportCSV);

  await loadLogs();
});

