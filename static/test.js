/* Voice screen: native voice UI on the ElevenLabs client SDK. */

import { Conversation } from "https://cdn.jsdelivr.net/npm/@elevenlabs/client/+esm";

const AGENT_ID = new URLSearchParams(location.search).get("agent")
  || "agent_5901kzg1ns03eyv8n4em0y9m97bn";

/* ---------- voice ---------- */

const talkBtn = document.getElementById("talk-btn");
const voiceStatus = document.getElementById("voice-status");
const transcript = document.getElementById("transcript");
let conversation = null;

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

function addLine(source, text) {
  transcript.hidden = false;
  const line = document.createElement("p");
  line.className = source === "user" ? "t-user" : "t-agent";
  line.textContent = text;
  transcript.append(line);
  transcript.scrollTop = transcript.scrollHeight;
}

function sessionOptions(connectionType) {
  return {
    agentId: AGENT_ID,
    connectionType,
    onConnect: () => setState("listening"),
    onDisconnect: () => { conversation = null; setState("idle"); },
    onModeChange: ({ mode }) => setState(mode === "speaking" ? "speaking" : "listening"),
    onMessage: ({ source, message }) => addLine(source, message),
    onError: () => { voiceStatus.textContent = "Connection error — tap to retry"; },
  };
}

async function start() {
  setState("connecting");
  try {
    await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
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
      setState("idle");
      voiceStatus.textContent = "Connection failed — tap to retry";
    }
  }
}

async function stop() {
  const c = conversation;
  conversation = null;
  setState("idle");
  await c?.endSession();
}

talkBtn.addEventListener("click", () => (conversation ? stop() : start()));

/* ---------- conditions strip ---------- */

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
