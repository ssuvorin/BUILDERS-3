/* Voice screen: native voice UI on the ElevenLabs client SDK. */

import { Conversation } from "https://cdn.jsdelivr.net/npm/@elevenlabs/client/+esm";

const AGENT_ID = new URLSearchParams(location.search).get("agent")
  || "agent_5901kzg1ns03eyv8n4em0y9m97bn";

/* ---------- voice ---------- */

const talkBtn = document.getElementById("talk-btn");
const voiceStatus = document.getElementById("voice-status");
const transcript = document.getElementById("transcript");
let conversation = null;
let starting = false;

const STATUS = {
  idle: "Tap to talk",
  connecting: "Connecting…",
  listening: "Listening…",
  speaking: "Tap to end, or just talk over it",
};

const orbStage = document.querySelector(".orb-stage");

function setState(state) {
  talkBtn.dataset.state = state;
  orbStage.dataset.live = state;
  voiceStatus.textContent = STATUS[state] ?? state;
  talkBtn.setAttribute("aria-label", state === "idle" ? "Start conversation" : "End conversation");
}

function cleanMessage(text) {
  return (text ?? "")
    .replace(/\[[a-z][a-z\s,'!?-]{0,40}\]/gi, "") // ElevenLabs v3 audio tags: [confident], [whispers]...
    .replace(/[ \t]{2,}/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/* live rendering: agent lines type out word-by-word, roughly in step with speech */
let typer = null;

function finishTyper() {
  if (!typer) return;
  clearInterval(typer.id);
  typer.el.textContent = typer.text;
  typer = null;
}

function typeInto(el, text) {
  finishTyper();
  const words = text.split(/(\s+)/);
  let i = 0;
  const id = setInterval(() => {
    i += 2;
    el.textContent = words.slice(0, i).join("");
    transcript.scrollTop = transcript.scrollHeight;
    if (i >= words.length) finishTyper();
  }, 90);
  typer = { id, el, text };
}

function showThinking() {
  if (document.getElementById("thinking")) return;
  transcript.hidden = false;
  const bubble = document.createElement("div");
  bubble.className = "msg msg-agent";
  bubble.id = "thinking";
  bubble.innerHTML = '<span class="msg-label">HeatSafe</span>' +
    '<p class="msg-text dots"><i></i><i></i><i></i></p>';
  transcript.append(bubble);
  transcript.scrollTop = transcript.scrollHeight;
}

function hideThinking() {
  document.getElementById("thinking")?.remove();
}

function addLine(source, text) {
  const clean = cleanMessage(text);
  if (!clean) return;
  transcript.hidden = false;
  hideThinking();
  const bubble = document.createElement("div");
  bubble.className = source === "user" ? "msg msg-user" : "msg msg-agent";
  const label = document.createElement("span");
  label.className = "msg-label";
  label.textContent = source === "user" ? "You" : "HeatSafe";
  const body = document.createElement("p");
  body.className = "msg-text";
  bubble.append(label, body);
  transcript.append(bubble);
  if (source === "user") {
    body.textContent = clean;
    showThinking(); // agent's turn — show it working until its line arrives
  } else {
    typeInto(body, clean);
  }
  transcript.scrollTop = transcript.scrollHeight;
}

function sessionOptions(connectionType) {
  return {
    agentId: AGENT_ID,
    connectionType,
    onConnect: () => setState("listening"),
    onDisconnect: () => { conversation = null; releaseLease(); hideThinking(); setState("idle"); },
    onModeChange: ({ mode }) => {
      if (mode === "speaking") hideThinking();
      setState(mode === "speaking" ? "speaking" : "listening");
    },
    onMessage: ({ source, message }) => addLine(source, message),
    onError: () => { voiceStatus.textContent = "Connection error — tap to retry"; },
  };
}

/* ---------- session lease (backend enforces one active session) ---------- */

let lease = null;          // { id, timer }

async function acquireLease() {
  const resp = await fetch("/api/voice-lease", { method: "POST" });
  if (resp.status === 409) return null; // all slots busy
  if (!resp.ok) throw new Error(`lease acquire failed: HTTP ${resp.status}`);
  const data = await resp.json();
  const interval = (data.heartbeat_seconds ?? 15) * 1000;
  const timer = setInterval(async () => {
    try {
      const hb = await fetch("/api/voice-lease/heartbeat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lease_id: data.lease_id }),
      });
      if (hb.status === 410) stop("Session expired — tap to start again");
    } catch { /* transient network blip; lease TTL is the arbiter */ }
  }, interval);
  return { id: data.lease_id, timer };
}

function releaseLease() {
  if (!lease) return;
  clearInterval(lease.timer);
  const body = JSON.stringify({ lease_id: lease.id });
  lease = null;
  navigator.sendBeacon?.("/api/voice-lease/release", new Blob([body], { type: "application/json" }))
    || fetch("/api/voice-lease/release", { method: "POST", headers: { "Content-Type": "application/json" }, body });
}

async function start() {
  if (starting || conversation) return; // one session per tab, ever
  starting = true;
  setState("connecting");
  let busy = false;
  try {
    lease = await acquireLease();
    busy = lease === null;
  } catch {
    lease = null;
  }
  if (!lease) {
    starting = false;
    setState("idle");
    voiceStatus.textContent = busy
      ? "All session slots are busy — try again in a moment"
      : "Could not reach the server — tap to retry";
    return;
  }
  try {
    await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    starting = false;
    releaseLease();
    setState("idle");
    voiceStatus.textContent = "Microphone blocked — allow mic access and tap again";
    return;
  }
  try {
    conversation = await Conversation.startSession(sessionOptions("webrtc"));
  } catch {
    try {
      conversation = await Conversation.startSession(sessionOptions("websocket"));
    } catch {
      conversation = null;
      voiceStatus.textContent = "Connection failed — tap to retry";
    }
  } finally {
    starting = false;
    if (!conversation) {
      releaseLease();
      if (talkBtn.dataset.state === "connecting") setState("idle");
    }
  }
}

async function stop(reason) {
  const c = conversation;
  conversation = null;
  releaseLease();
  setState("idle");
  if (reason) voiceStatus.textContent = reason;
  await c?.endSession();
}

talkBtn.addEventListener("click", () => {
  if (starting) return; // ignore taps while a session is being established
  conversation ? stop() : start();
});

window.addEventListener("pagehide", releaseLease);

/* ---------- conditions strip ---------- */

const badge = document.getElementById("verdict-badge");

async function checkConditions() {
  badge.dataset.state = "loading";
  badge.textContent = "CHECKING…";
  try {
    const resp = await fetch("/tools/check_weather", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-HeatSafe-UI": "1" },
      body: JSON.stringify({ activity: "external work" }),
    });
    const data = await resp.json();
    const state = data.verdict ?? "unknown";
    badge.dataset.state = state;
    badge.textContent = { go: "GO", restricted: "RESTRICTED", "no-go": "NO-GO", unknown: "UNVERIFIED" }[state] ?? state;
    set("s-wind", data.wind_sustained_mph != null ? `wind ${data.wind_sustained_mph} mph` : "");
    set("s-gust", data.wind_gust_mph != null ? `gusts ${data.wind_gust_mph} mph` : "");
    set("s-temp", data.temp_c != null ? `${data.temp_c} °C` : "");
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
