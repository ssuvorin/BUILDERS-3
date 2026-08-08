/* Test console: compact conditions strip + widget + tap-to-copy questions. */

const AGENT_ID = new URLSearchParams(location.search).get("agent")
  || "agent_5901kzg1ns03eyv8n4em0y9m97bn";

/* widget */
const widget = document.createElement("elevenlabs-convai");
widget.setAttribute("agent-id", AGENT_ID);
document.body.append(widget);
const script = document.createElement("script");
script.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
script.async = true;
document.body.append(script);

/* conditions strip */
const badge = document.getElementById("verdict-badge");

async function checkConditions() {
  badge.dataset.state = "loading";
  badge.textContent = "CHECKING…";
  try {
    const resp = await fetch("/tools/check_weather", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activity: "external work" }),
    });
    const data = await resp.json();
    const state = data.verdict ?? "unknown";
    badge.dataset.state = state;
    badge.textContent = { go: "GO", restricted: "RESTRICTED", "no-go": "NO-GO", unknown: "UNVERIFIED" }[state] ?? state;
    set("s-wind", data.wind_sustained_mph != null ? `wind ${data.wind_sustained_mph} mph` : "wind —");
    set("s-gust", data.wind_gust_mph != null ? `gusts ${data.wind_gust_mph} mph` : "gusts —");
    set("s-temp", data.temp_c != null ? `temp ${data.temp_c} °C` : "temp —");
  } catch {
    badge.dataset.state = "unknown";
    badge.textContent = "UNVERIFIED";
  }
}

function set(id, text) {
  document.getElementById(id).textContent = text;
}

document.getElementById("refresh-btn").addEventListener("click", checkConditions);
checkConditions();

/* tap-to-copy questions */
document.getElementById("q-grid").addEventListener("click", async (e) => {
  const btn = e.target.closest(".q");
  if (!btn) return;
  const text = btn.childNodes[0].textContent.trim();
  try { await navigator.clipboard.writeText(text); } catch { /* non-secure ctx */ }
  btn.classList.add("copied");
  setTimeout(() => btn.classList.remove("copied"), 900);
});
