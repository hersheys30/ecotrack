function el(id) {
  return document.getElementById(id);
}

function setStatus(kind, msg) {
  const box = el("logStatus");
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

function fmtKg(v) {
  return `${Number(v || 0).toFixed(2)} kg`;
}

async function loadFactors(scope) {
  const factors = await window.EcoTrackAPI.apiFetch(`/emission-factors${scope ? `?scope=${scope}` : ""}`);
  return factors;
}

function uniqActivityTypes(factors) {
  const set = new Set();
  for (const f of factors) set.add(f.activity_type);
  return [...set].sort();
}

async function refreshActivityTypes() {
  const scope = Number(el("scope").value);
  setStatus("", "");
  try {
    const factors = await loadFactors(scope);
    const acts = uniqActivityTypes(factors);
    const sel = el("activity_type");
    sel.innerHTML = acts.map((a) => `<option value="${a}">${a}</option>`).join("");
    const first = factors.find((f) => f.activity_type === sel.value);
    el("factorHint").textContent = first ? `${first.factor_value} kgCO2e/${first.unit}` : "No factor found";
  } catch (e) {
    setStatus("err", `<b>Couldn’t load emission factors.</b> ${e.message || e}`);
  }
}

async function updateFactorHint() {
  const scope = Number(el("scope").value);
  const act = el("activity_type").value;
  const factors = await loadFactors(scope);
  const factor = factors.find((f) => f.activity_type === act);
  el("factorHint").textContent = factor ? `${factor.factor_value} kgCO2e/${factor.unit}` : "No factor found";
}

async function submitLog(e) {
  e.preventDefault();
  setStatus("", "");

  const payload = {
    scope: Number(el("scope").value),
    activity_type: el("activity_type").value,
    quantity: Number(el("quantity").value),
    unit: el("unit").value,
    date: el("date").value,
    notes: el("notes").value || null,
  };

  if (!Number.isFinite(payload.quantity) || payload.quantity <= 0) {
    setStatus("err", "<b>Check quantity.</b> Must be a number greater than 0.");
    el("quantity").focus();
    return;
  }
  if (!payload.date) {
    setStatus("err", "<b>Pick a date.</b> This is required for reporting.");
    el("date").focus();
    return;
  }

  const btn = document.querySelector("#formLog button[type='submit']");
  btn.disabled = true;
  btn.textContent = "Saving…";
  try {
    const res = await window.EcoTrackAPI.apiFetch("/emissions/log", { method: "POST", body: payload });
    el("calculated").textContent = fmtKg(res.emissions.calculated_co2e);
    setStatus("ok", `<b>Saved.</b> Calculated CO2e: <span class="mono">${fmtKg(res.emissions.calculated_co2e)}</span>`);
  } catch (err) {
    setStatus("err", `<b>Couldn’t save.</b> ${err.message || err}`);
  } finally {
    btn.disabled = false;
    btn.textContent = "Calculate & Save";
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  window.EcoTrackAuth.requireAuth();
  window.EcoTrackAuth.setActivePageNav();

  el("btnLogout").addEventListener("click", window.EcoTrackAuth.logout);
  el("date").value = todayISO();

  el("scope").addEventListener("change", refreshActivityTypes);
  el("activity_type").addEventListener("change", updateFactorHint);
  el("formLog").addEventListener("submit", submitLog);

  await refreshActivityTypes();
});

