function fmtKg(v) {
  const n = Number(v || 0);
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M kg`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(2)}k kg`;
  return `${n.toFixed(2)} kg`;
}

function el(id) {
  return document.getElementById(id);
}

let charts = {};
let lastFactors = [];

function destroyCharts() {
  Object.values(charts).forEach((c) => {
    try {
      c.destroy();
    } catch {}
  });
  charts = {};
}

function setLoading(isLoading) {
  document.body.classList.toggle("is-loading", !!isLoading);
  const show = document.querySelectorAll(".show-while-loading");
  const hide = document.querySelectorAll(".hide-while-loading");
  show.forEach((n) => (n.style.display = isLoading ? "" : "none"));
  hide.forEach((n) => (n.style.display = isLoading ? "none" : ""));
}

function renderSummary(data) {
  el("kpiTotal").textContent = fmtKg(data.total_co2e);

  const s1 = data.by_scope["Scope 1"] ?? 0;
  const s2 = data.by_scope["Scope 2"] ?? 0;
  const s3 = data.by_scope["Scope 3"] ?? 0;
  el("chipS1").textContent = fmtKg(s1);
  el("chipS2").textContent = fmtKg(s2);
  el("chipS3").textContent = fmtKg(s3);
}

function renderRecent(rows) {
  const tbody = el("recentBody");
  tbody.innerHTML = "";
  for (const r of rows || []) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="mono">#${r.id}</td>
      <td>Scope ${r.scope}</td>
      <td>${r.activity_type}</td>
      <td class="mono">${Number(r.quantity).toFixed(2)} ${r.unit}</td>
      <td class="mono">${fmtKg(r.calculated_co2e)}</td>
      <td class="mono">${r.date}</td>
    `;
    tbody.appendChild(tr);
  }
}

function renderCharts(data) {
  destroyCharts();
  const p = window.EcoTrackCharts.palette();

  // Bar: emissions by scope over time (stacked)
  const months = (data.monthly_by_scope || []).map((r) => r.month);
  const s1 = (data.monthly_by_scope || []).map((r) => r["Scope 1"] || 0);
  const s2 = (data.monthly_by_scope || []).map((r) => r["Scope 2"] || 0);
  const s3 = (data.monthly_by_scope || []).map((r) => r["Scope 3"] || 0);

  const barOpt = window.EcoTrackCharts.baseChartOptions();
  barOpt.scales.x.stacked = true;
  barOpt.scales.y.stacked = true;
  barOpt.scales.y.title = { display: true, text: "kgCO2e", color: p.muted };

  charts.byScope = new Chart(el("barByScope"), {
    type: "bar",
    data: {
      labels: months,
      datasets: [
        { label: "Scope 1", data: s1, backgroundColor: p.s1 },
        { label: "Scope 2", data: s2, backgroundColor: p.s2 },
        { label: "Scope 3", data: s3, backgroundColor: p.s3 },
      ],
    },
    options: barOpt,
  });

  // Pie: breakdown by activity type
  const actLabels = (data.by_activity_type || []).map((r) => r.activity_type);
  const actValues = (data.by_activity_type || []).map((r) => r.co2e);
  const pieColors = actLabels.map((_, i) => {
    const hues = [96, 84, 110, 70, 102, 120, 90, 60, 140, 160, 40, 20];
    const h = hues[i % hues.length];
    return `hsla(${h}, 18%, ${42 + (i % 4) * 6}%, .95)`;
  });

  const pieOpt = window.EcoTrackCharts.baseChartOptions();
  delete pieOpt.scales;
  pieOpt.plugins.legend.position = "bottom";

  charts.byActivity = new Chart(el("pieActivity"), {
    type: "doughnut",
    data: {
      labels: actLabels,
      datasets: [{ data: actValues, backgroundColor: pieColors, borderColor: "rgba(0,0,0,.0)" }],
    },
    options: pieOpt,
  });

  // Line: monthly total trend
  const totals = months.map((_, i) => (s1[i] || 0) + (s2[i] || 0) + (s3[i] || 0));
  const lineOpt = window.EcoTrackCharts.baseChartOptions();
  lineOpt.scales.y.title = { display: true, text: "kgCO2e", color: p.muted };

  charts.trend = new Chart(el("lineTrend"), {
    type: "line",
    data: {
      labels: months,
      datasets: [
        {
          label: "Total",
          data: totals,
          borderColor: p.s2,
          backgroundColor: "rgba(169,192,135,.12)",
          tension: 0.35,
          fill: true,
          pointRadius: 2,
        },
      ],
    },
    options: lineOpt,
  });
}

function setStatus(kind, msg) {
  const box = el("dashStatus");
  if (!msg) {
    box.style.display = "none";
    return;
  }
  box.style.display = "block";
  box.className = `notice ${kind === "err" ? "err" : kind === "ok" ? "ok" : ""}`;
  box.innerHTML = msg;
}

function todayISO() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function setQuickStatus(kind, msg) {
  const box = el("quickStatus");
  if (!msg) {
    box.style.display = "none";
    return;
  }
  box.style.display = "block";
  box.className = `notice ${kind === "err" ? "err" : kind === "ok" ? "ok" : ""}`;
  box.innerHTML = msg;
}

function openModal() {
  const m = el("quickModal");
  m.classList.add("open");
  m.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  const m = el("quickModal");
  m.classList.remove("open");
  m.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  setQuickStatus("", "");
}

function uniqActivityTypes(factors) {
  const set = new Set();
  for (const f of factors) set.add(f.activity_type);
  return [...set].sort();
}

async function loadFactors(scope) {
  return await window.EcoTrackAPI.apiFetch(`/emission-factors${scope ? `?scope=${scope}` : ""}`);
}

function findFactor(scope, activityType) {
  return (lastFactors || []).find((f) => Number(f.scope) === Number(scope) && f.activity_type === activityType);
}

function updateQuickFactorHint() {
  const scope = Number(el("q_scope").value);
  const act = el("q_activity").value;
  const factor = findFactor(scope, act);
  el("q_factorHint").textContent = factor ? `${factor.factor_value} kgCO2e/${factor.unit}` : "No factor found";
}

function estimateQuickCO2e() {
  const scope = Number(el("q_scope").value);
  const act = el("q_activity").value;
  const factor = findFactor(scope, act);
  const qty = Number(el("q_qty").value || 0);
  const unit = el("q_unit").value;
  if (!factor || !qty || qty <= 0) {
    el("q_result").value = "—";
    return;
  }
  // quick estimate (backend is source of truth; this is just feedback)
  el("q_result").value = "Calculated on save";
  if (String(unit).trim().toLowerCase() === String(factor.unit).trim().toLowerCase()) {
    el("q_result").value = fmtKg(qty * Number(factor.factor_value));
  }
}

async function refreshQuickActivities() {
  const scope = Number(el("q_scope").value);
  lastFactors = await loadFactors(scope);
  const sel = el("q_activity");
  const acts = uniqActivityTypes(lastFactors);
  sel.innerHTML = acts.map((a) => `<option value="${a}">${a}</option>`).join("");
  updateQuickFactorHint();
  estimateQuickCO2e();
}

async function submitQuick(e) {
  e.preventDefault();
  setQuickStatus("", "");

  const qty = Number(el("q_qty").value);
  if (!Number.isFinite(qty) || qty <= 0) {
    setQuickStatus("err", "<b>Check quantity.</b> Must be a number greater than 0.");
    return;
  }
  if (!el("q_date").value) {
    setQuickStatus("err", "<b>Pick a date.</b> This is required for reporting.");
    return;
  }

  const payload = {
    scope: Number(el("q_scope").value),
    activity_type: el("q_activity").value,
    quantity: qty,
    unit: el("q_unit").value,
    date: el("q_date").value,
    notes: el("q_notes").value || null,
  };

  const btn = el("btnModalSave");
  btn.disabled = true;
  btn.textContent = "Saving…";
  try {
    const res = await window.EcoTrackAPI.apiFetch("/emissions/log", { method: "POST", body: payload });
    setQuickStatus("ok", `<b>Saved.</b> CO2e: <span class="mono">${fmtKg(res.emissions.calculated_co2e)}</span>`);
    await loadDashboard();
    setTimeout(closeModal, 500);
  } catch (err) {
    setQuickStatus("err", `<b>Couldn’t save.</b> ${err.message || err}`);
  } finally {
    btn.disabled = false;
    btn.textContent = "Save";
  }
}

async function loadDashboard() {
  setStatus("", "");
  setLoading(true);
  try {
    const data = await window.EcoTrackAPI.apiFetch("/dashboard/summary");
    renderSummary(data);
    renderCharts(data);
    renderRecent(data.recent_activity || []);
    setStatus("ok", `<b>Up to date.</b> Seeded factors are ready — log an activity to see the charts move.`);
  } catch (e) {
    setStatus("err", `<b>Couldn’t load dashboard.</b> ${e.message || e}`);
  } finally {
    setLoading(false);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.EcoTrackAuth.requireAuth();
  window.EcoTrackAuth.setActivePageNav();
  document.getElementById("btnLogout").addEventListener("click", window.EcoTrackAuth.logout);
  document.getElementById("btnRefresh").addEventListener("click", loadDashboard);
  document.getElementById("btnQuickLog").addEventListener("click", () => {
    openModal();
    refreshQuickActivities().catch((e) => setQuickStatus("err", `<b>Couldn’t load factors.</b> ${e.message || e}`));
  });
  document.getElementById("btnQuickLog2").addEventListener("click", () => {
    openModal();
    refreshQuickActivities().catch((e) => setQuickStatus("err", `<b>Couldn’t load factors.</b> ${e.message || e}`));
  });
  document.getElementById("btnModalClose").addEventListener("click", closeModal);
  document.getElementById("btnModalCancel").addEventListener("click", closeModal);
  document.getElementById("quickModal").addEventListener("click", (e) => {
    if (e.target && e.target.id === "quickModal") closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
  el("q_date").value = todayISO();
  el("q_scope").addEventListener("change", () => refreshQuickActivities().catch(() => {}));
  el("q_activity").addEventListener("change", () => {
    updateQuickFactorHint();
    estimateQuickCO2e();
  });
  el("q_qty").addEventListener("input", estimateQuickCO2e);
  el("q_unit").addEventListener("change", estimateQuickCO2e);
  el("quickForm").addEventListener("submit", submitQuick);
  loadDashboard();
});

