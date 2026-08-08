/* HeatSafe field view.
 *
 * One button. Tap once, the session opens and stays open — continuous,
 * interruptible — until tapped again.
 *
 * There is no wake word, and that is a decision rather than a gap. A browser
 * cannot listen before the user grants microphone access and interacts, so
 * "Hey HeatSafe" would need an on-device wake-word engine. It would also be the
 * wrong choice for the user: on a site at 95 dB a spoken trigger misfires
 * constantly, and a large target that works through a glove is more reliable.
 */

const AGENT_ID =
  new URLSearchParams(location.search).get("agent") ||
  "agent_5901kzg1ns03eyv8n4em0y9m97bn";

const STALE_AFTER_MS = 10 * 60 * 1000; // MER-SOP-021 readings go stale (eval B3 #13)

const mic = document.getElementById("fx-mic");
const prompt = document.getElementById("fx-prompt");
const sub = document.getElementById("fx-sub");
const badge = document.getElementById("fx-badge");
const rule = document.getElementById("fx-rule");
const stamp = document.getElementById("fx-stamp");
const host = document.getElementById("fx-widget-host");

/* ── conditions ─────────────────────────────────────────────────────── */

const STATE_COLOUR = {
  go: "var(--fx-go)",
  restricted: "var(--fx-restricted)",
  "no-go": "var(--fx-stop)",
  unknown: "var(--fx-unknown)",
};
const STATE_LABEL = { go: "GO", restricted: "RESTRICTED", "no-go": "STOP", unknown: "UNVERIFIED" };

let readingAt = null;

async function checkConditions() {
  badge.dataset.state = "loading";
  badge.textContent = "CHECKING";
  try {
    const resp = await fetch("/tools/check_weather", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activity: "external work" }),
    });
    if (!resp.ok) throw new Error(String(resp.status));
    paint(await resp.json());
  } catch {
    paint({
      verdict: "unknown",
      reason: "No reading. Do not assume conditions are fine — check with your supervisor.",
    });
  }
}

function paint(data) {
  const state = data.verdict ?? "unknown";
  document.documentElement.style.setProperty("--fx-state", STATE_COLOUR[state] ?? STATE_COLOUR.unknown);
  badge.textContent = STATE_LABEL[state] ?? state.toUpperCase();

  const hasReading = data.temp_c != null;
  document.getElementById("fx-conditions").dataset.reading = hasReading ? "yes" : "no";
  setText("fx-temp", hasReading ? String(data.temp_c) : "no reading");
  setText("fx-wind", data.wind_sustained_mph != null ? `${data.wind_sustained_mph} mph` : "—");
  setText("fx-gust", data.wind_gust_mph != null ? `${data.wind_gust_mph} mph` : "—");

  // Lead with the binding rule, not a summary. The worker needs the reason.
  const reasons = data.reasons ?? (data.reason ? [data.reason] : []);
  rule.textContent = reasons[0] ?? "Conditions are within all policy limits for external work.";
  if (data.weather_note) rule.textContent += ` ${data.weather_note}`;

  const src = document.getElementById("fx-source");
  src.textContent = data.policy_source
    ? `${data.policy_source} · HeatSafe advises, your supervisor decides.`
    : "HeatSafe advises. Your supervisor decides.";

  readingAt = data.temp_c != null ? Date.now() : null;
  tickStamp();
}

function tickStamp() {
  if (!readingAt) { stamp.textContent = ""; return; }
  const age = Date.now() - readingAt;
  const mins = Math.floor(age / 60000);
  const stale = age >= STALE_AFTER_MS;
  stamp.dataset.stale = stale ? "true" : "false";
  stamp.textContent = stale
    ? `Reading ${mins} min old — stale, tap ↻ before acting.`
    : mins < 1
      ? "Live reading."
      : `Read ${mins} min ago.`;
}

function setText(id, v) { document.getElementById(id).textContent = v; }

/* ── the voice session ──────────────────────────────────────────────── */

const widget = document.createElement("elevenlabs-convai");
widget.setAttribute("agent-id", AGENT_ID);
host.append(widget);

const script = document.createElement("script");
script.src = "https://unpkg.com/@elevenlabs/convai-widget-embed";
script.async = true;
script.onerror = () => {
  setState("idle");
  prompt.textContent = "Voice unavailable";
  sub.textContent = "The voice widget could not load on this network. Conditions above are still live.";
};
document.body.append(script);

const COPY = {
  idle: ["Tap once. Then just talk.", "Stays listening until you tap again. Interrupt any time."],
  connecting: ["Connecting…", "Allow the microphone when your phone asks."],
  live: ["Listening", "Just talk. Tap again to end."],
};

function setState(state) {
  mic.dataset.state = state;
  const [p, s] = COPY[state] ?? COPY.idle;
  prompt.textContent = p;
  sub.textContent = s;
  mic.setAttribute("aria-label", state === "live" ? "End the conversation" : "Start talking to HeatSafe");
}

/* The widget owns its own trigger inside a shadow root. Reach in and press it so
 * our button is the only thing the worker sees. If that fails — different widget
 * build, closed shadow root — reveal the real widget rather than leave a dead
 * button. */
function pressWidget() {
  const root = widget.shadowRoot;
  if (!root) return false;
  const target = root.querySelector('button, [role="button"]');
  if (!target) return false;
  target.click();
  return true;
}

let live = false;

mic.addEventListener("click", () => {
  if (live) {
    pressWidget();
    live = false;
    setState("idle");
    return;
  }
  setState("connecting");
  const pressed = pressWidget();
  if (!pressed) {
    host.dataset.visible = "true";
    setState("idle");
    prompt.textContent = "Tap the voice bubble";
    sub.textContent = "Bottom right. This build of the widget needs its own control.";
    return;
  }
  live = true;
  // The widget does not expose a reliable ready event across builds, so the
  // listening state is shown once the session has had a moment to open.
  setTimeout(() => { if (live) setState("live"); }, 900);
});

document.getElementById("fx-refresh").addEventListener("click", checkConditions);
setInterval(tickStamp, 10000);
setInterval(checkConditions, 5 * 60 * 1000); // keep the reading fresh on screen
setState("idle");
checkConditions();
