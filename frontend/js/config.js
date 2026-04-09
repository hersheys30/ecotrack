// Central place to tweak API base URL.
// - file:// (opening HTML from disk): default to local API on 8001.
// - Same-origin deploy (Docker/Render): use current origin so /auth/* hits the FastAPI app.
(function () {
  function defaultApiBase() {
    var stored = localStorage.getItem("ECOTRACK_API_BASE_URL");
    if (stored) return stored;
    if (window.location.protocol === "file:") return "http://127.0.0.1:8001";
    return window.location.origin;
  }
  window.ECOTRACK_CONFIG = {
    API_BASE_URL: defaultApiBase(),
  };
})();

