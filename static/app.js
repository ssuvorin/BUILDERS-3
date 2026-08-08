/* HeatSafe promo page: live conditions panel. Voice testing lives at /test. */

/* ---------- live conditions ---------- */

const badge = document.getElementById("verdict-badge");
const note = document.getElementById("verdict-note");
const readings = document.getElementById("readings");
const reasons = document.getElementById("reasons");
const sourceLine = document.getElementById("policy-source");

async function checkConditions() {
  badge.dataset.state = "loading";
  badge.textContent = "CHECKING…";
  note.textContent = "Fetching live weather via context.dev…";
  reasons.replaceChildren();
  try {
    const resp = await fetch("/tools/check_weather", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-HeatSafe-UI": "1" },
      body: JSON.stringify({ activity: "external work" }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    render(await resp.json());
  } catch {
    render({ verdict: "unknown", reason: "Weather source unavailable — never assume conditions are fine." });
  }
}

function render(data) {
  const state = data.verdict ?? "unknown";
  badge.dataset.state = state;
  badge.textContent = { go: "GO", restricted: "RESTRICTED", "no-go": "NO-GO", unknown: "UNVERIFIED" }[state] ?? state.toUpperCase();
  note.textContent = {
    go: "External work is within policy limits right now.",
    restricted: "Restricted band — limits apply, see reasons.",
    "no-go": "External work must stop under company policy.",
    unknown: data.reason ?? "Conditions cannot be verified.",
  }[state];

  const hasReadings = typeof data.wind_sustained_mph === "number";
  readings.hidden = !hasReadings;
  if (hasReadings) {
    setText("r-wind", `${data.wind_sustained_mph} mph`);
    setText("r-gust", data.wind_gust_mph ? `${data.wind_gust_mph} mph` : "—");
    setText("r-temp", data.temp_c != null ? `${data.temp_c} °C` : "—");
  }

  for (const r of data.reasons ?? []) {
    const li = document.createElement("li");
    li.textContent = r;
    reasons.append(li);
  }
  const src = data.policy_source ?? data.policy_thresholds_still_valid?.source;
  sourceLine.textContent = src
    ? `Thresholds: ${src} · Weather: live via context.dev · Final stop/go call: site supervisor`
    : "Final stop/go call: site supervisor";
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

document.getElementById("refresh-btn").addEventListener("click", checkConditions);
checkConditions();

/* ---------- hero spotlight follows the cursor ---------- */

const visual = document.getElementById("hero-visual");
const spotlight = document.getElementById("spotlight");
if (visual && spotlight && matchMedia("(hover: hover)").matches) {
  visual.addEventListener("mousemove", (e) => {
    const rect = visual.getBoundingClientRect();
    spotlight.style.left = `${e.clientX - rect.left}px`;
    spotlight.style.top = `${e.clientY - rect.top}px`;
  });
}
