#!/usr/bin/env node
/**
 * Live source probe — HeatSafe Voice Copilot
 *
 * Verifies every external data source we plan to depend on is reachable RIGHT NOW
 * and prints a real sample. Run before the demo. If a source is red, we either fix
 * it or the agent must say it cannot verify conditions (eval B3 #15) — we never
 * assume conditions are fine.
 *
 *   node scripts/check_sources.mjs
 *
 * No API keys, no dependencies. Node 18+.
 */

// Meridian Construction's site. Business Bay, Dubai.
const SITE = { name: "Dubai (Business Bay)", lat: 25.1857, lon: 55.2766 };

const TIMEOUT_MS = 12000;

async function probe(label, url, opts = {}) {
  const started = Date.now();
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      redirect: "follow",
      headers: { "User-Agent": "HeatSafe-source-check/1.0", ...(opts.headers || {}) },
    });
    const ms = Date.now() - started;
    if (!res.ok) return { label, url, ok: false, ms, note: `HTTP ${res.status}` };
    const body = opts.json ? await res.json() : await res.text();
    return { label, url, ok: true, ms, body };
  } catch (err) {
    return { label, url, ok: false, ms: Date.now() - started, note: err.name === "AbortError" ? "timeout" : err.message };
  } finally {
    clearTimeout(t);
  }
}

const c = { green: (s) => `\x1b[32m${s}\x1b[0m`, red: (s) => `\x1b[31m${s}\x1b[0m`, dim: (s) => `\x1b[2m${s}\x1b[0m`, bold: (s) => `\x1b[1m${s}\x1b[0m` };

function line(r, extra = "") {
  const status = r.ok ? c.green("  UP  ") : c.red(" DOWN ");
  console.log(`${status} ${r.label.padEnd(34)} ${c.dim(`${r.ms}ms`)} ${extra || (r.ok ? "" : c.red(r.note))}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// TIER A — live conditions (numbers the agent speaks aloud)
// ─────────────────────────────────────────────────────────────────────────────
async function tierA() {
  console.log(c.bold("\nTIER A — live conditions\n"));

  // Open-Meteo intermittently times out from conference wifi — retry once before
  // calling it down, otherwise the demo reports a false blocker.
  let om = await probe(
    "Open-Meteo (primary)",
    `https://api.open-meteo.com/v1/forecast?latitude=${SITE.lat}&longitude=${SITE.lon}` +
      `&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,wind_gusts_10m,uv_index,visibility,weather_code` +
      `&wind_speed_unit=mph&timezone=Asia%2FDubai`,
    { json: true }
  );
  if (!om.ok) {
    om = await probe(
      "Open-Meteo (primary, retry)",
      `https://api.open-meteo.com/v1/forecast?latitude=${SITE.lat}&longitude=${SITE.lon}` +
        `&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,wind_gusts_10m,uv_index,visibility,weather_code` +
        `&wind_speed_unit=mph&timezone=Asia%2FDubai`,
      { json: true }
    );
  }
  if (om.ok) {
    const x = om.body.current;
    line(om);
    console.log(
      c.dim(
        `        temp ${x.temperature_2m}°C · feels ${x.apparent_temperature}°C · humidity ${x.relative_humidity_2m}% · ` +
          `wind ${x.wind_speed_10m}mph · gusts ${x.wind_gusts_10m}mph · UV ${x.uv_index} · vis ${x.visibility}m`
      )
    );
    console.log(c.dim(`        reading time: ${x.time} (Asia/Dubai)`));
  } else line(om);

  const wttr = await probe("wttr.in (fallback)", `https://wttr.in/Dubai?format=j1`, { json: true });
  if (wttr.ok) {
    const x = wttr.body.current_condition?.[0] || {};
    line(wttr);
    console.log(c.dim(`        temp ${x.temp_C}°C · wind ${x.windspeedMiles}mph · humidity ${x.humidity}% · ${x.weatherDesc?.[0]?.value}`));
  } else line(wttr);

  return { om, wttr };
}

// ─────────────────────────────────────────────────────────────────────────────
// TIER B — official regional authority (outranks any weather API)
// ─────────────────────────────────────────────────────────────────────────────
async function tierB() {
  console.log(c.bold("\nTIER B — official UAE authority\n"));
  const targets = [
    ["NCM — UAE met authority", "https://www.ncm.gov.ae/?lang=en"],
    ["u.ae — health & safety at work", "https://u.ae/en/information-and-services/jobs/health-and-safety-at-workplace"],
    ["u.ae — working hours", "https://u.ae/en/information-and-services/jobs/employment-in-the-private-sector/working-hours"],
    ["MOHRE — midday break guidance", "https://www.mohre.gov.ae/en/guidance-and-awareness-portal-new/the-midday-break"],
    ["MOHRE", "https://www.mohre.gov.ae/en/home.aspx"],
    ["Dubai Municipality", "https://www.dm.gov.ae/"],
  ];
  const out = [];
  for (const [label, url] of targets) {
    const r = await probe(label, url);
    line(r, r.ok ? c.dim(`${(r.body.length / 1024).toFixed(0)}kb html`) : "");
    out.push(r);
  }
  return out;
}

// ─────────────────────────────────────────────────────────────────────────────
// TIER C — official guidance (ranked below company SOPs)
// ─────────────────────────────────────────────────────────────────────────────
async function tierC() {
  console.log(c.bold("\nTIER C — official guidance / standards\n"));
  const targets = [
    ["HSE — work at height", "https://www.hse.gov.uk/work-at-height/index.htm"],
    ["HSE — scaffolding", "https://www.hse.gov.uk/construction/safetytopics/scaffoldinginfo.htm"],
    ["legislation.gov.uk — WAHR 2005", "https://www.legislation.gov.uk/uksi/2005/735/contents/made"],
    ["NASC (scaffolding standards)", "https://nasc.org.uk/"],
    ["NIOSH heat stress", "https://www.cdc.gov/niosh/topics/heatstress/"],
  ];
  const out = [];
  for (const [label, url] of targets) {
    const r = await probe(label, url);
    line(r, r.ok ? c.dim(`${(r.body.length / 1024).toFixed(0)}kb html`) : "");
    out.push(r);
  }
  return out;
}

// ─────────────────────────────────────────────────────────────────────────────
// The midday-break clock — live regional-law check, today
// ─────────────────────────────────────────────────────────────────────────────
function middayBreakStatus() {
  console.log(c.bold("\nREGIONAL LAW — midday break window\n"));
  const now = new Date(new Date().toLocaleString("en-US", { timeZone: "Asia/Dubai" }));
  const mins = now.getHours() * 60 + now.getMinutes();
  const inSeason = (() => {
    const m = now.getMonth() + 1, d = now.getDate();
    return (m > 6 || (m === 6 && d >= 15)) && (m < 9 || (m === 9 && d <= 15));
  })();
  const inWindow = mins >= 12 * 60 + 30 && mins < 15 * 60;
  const hhmm = now.toTimeString().slice(0, 5);

  console.log(c.dim(`        Dubai local time: ${hhmm}`));
  console.log(c.dim(`        seasonal window (15 Jun – 15 Sep): ${inSeason ? "ACTIVE" : "inactive"}`));
  console.log(c.dim(`        daily window (12:30 – 15:00):      ${inWindow ? "INSIDE" : "outside"}`));
  console.log(
    inSeason && inWindow
      ? c.red("        ⇒ outdoor work restricted RIGHT NOW under the UAE midday break rule")
      : c.green("        ⇒ outside the restricted window")
  );
  console.log(
    c.dim(
      "\n        NOTE: this clock is a convenience only. The authoritative wording lives at u.ae\n" +
        "        and MOHRE and must be retrieved and quoted, not asserted from code. The agent\n" +
        "        names the source; it never states a legal threshold on its own authority."
    )
  );
  return { inSeason, inWindow };
}

// ─────────────────────────────────────────────────────────────────────────────
// Cross-check: do our two "live" sources agree? They feed safety decisions.
// ─────────────────────────────────────────────────────────────────────────────
function crossCheck(a) {
  console.log(c.bold("\nCROSS-CHECK — do the sources agree?\n"));
  if (!a.om.ok || !a.wttr.ok) return console.log(c.dim("        skipped, a source is down"));
  const om = a.om.body.current;
  const wt = a.wttr.body.current_condition[0];
  const dTemp = Math.abs(om.temperature_2m - Number(wt.temp_C));
  const omKmh = om.wind_speed_10m * 1.60934;
  const dWind = Math.abs(omKmh - Number(wt.windspeedKmph));

  console.log(`        temp   Open-Meteo ${om.temperature_2m}°C  vs  wttr.in ${wt.temp_C}°C   ${dTemp >= 3 ? c.red(`Δ ${dTemp.toFixed(1)}°C`) : c.green(`Δ ${dTemp.toFixed(1)}°C`)}`);
  console.log(`        wind   Open-Meteo ${omKmh.toFixed(1)}km/h vs wttr.in ${wt.windspeedKmph}km/h  ${dWind >= 5 ? c.red(`Δ ${dWind.toFixed(1)}`) : c.green(`Δ ${dWind.toFixed(1)}`)}`);

  const wttrHasGusts = "WindGustKmph" in wt || "windGustKmph" in wt;
  console.log(`        gusts  Open-Meteo ${(om.wind_gusts_10m * 1.60934).toFixed(1)}km/h vs wttr.in ${wttrHasGusts ? "present" : c.red("NOT PROVIDED")}`);
  if (!wttrHasGusts) {
    console.log(
      c.red(
        "\n        ⚠ MC-POL-014 says: \"Gusts count: if gusts exceed the limit for the\n" +
          "          activity, treat the limit as exceeded even if the sustained wind is\n" +
          "          below it.\" wttr.in does not publish a gust figure, so a gust-aware\n" +
          "          verdict cannot be sourced from it. Use Open-Meteo for wind."
      )
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Live verdict against the real thresholds in demo-data/meridian-wind-weather-policy.md
// Rehearsal tool: tells you what the agent SHOULD say right now.
// ─────────────────────────────────────────────────────────────────────────────
function verdicts(a, mb) {
  console.log(c.bold("\nLIVE VERDICT vs MC-POL-014 (rehearsal)\n"));
  if (!a.om.ok) return console.log(c.dim("        skipped, no reading"));
  const x = a.om.body.current;
  const windKmh = x.wind_speed_10m * 1.60934;
  const gustKmh = x.wind_gusts_10m * 1.60934;
  const worst = Math.max(windKmh, gustKmh); // SOP: gusts count

  console.log(c.dim(`        reading: ${x.temperature_2m}°C (feels ${x.apparent_temperature}°C) · wind ${windKmh.toFixed(1)}km/h · gusts ${gustKmh.toFixed(1)}km/h\n`));

  for (const [activity, limit] of [["Work at height / scaffolding", 30], ["Crane and hoist operations", 25], ["Sheet materials at height", 20]]) {
    const stop = worst >= limit;
    console.log(`        ${stop ? c.red("STOP") : c.green(" GO ")}  ${activity.padEnd(30)} limit ${limit}km/h, worst reading ${worst.toFixed(1)}km/h`);
  }

  const t = x.temperature_2m;
  if (t >= 50) console.log(c.red(`\n        HEAT: ${t}°C ≥ 50°C — all outdoor work suspended (MC-POL-014)`));
  else if (t >= 45) console.log(c.red(`\n        HEAT: ${t}°C ≥ 45°C — site manager sign-off + shaded rest every 45min (MC-POL-014)`));
  else console.log(c.dim(`\n        HEAT: ${t}°C — below the 45°C sign-off threshold (${(45 - t).toFixed(1)}°C of headroom)`));

  if (mb.inSeason && mb.inWindow) console.log(c.red("        MIDDAY BREAK: active now — no outdoor work until 15:00 (MOHRE)"));
  else if (mb.inSeason) console.log(c.dim("        MIDDAY BREAK: in season, outside the 12:30–15:00 window"));

  console.log(c.dim("\n        The agent reports these and names MC-POL-014. The supervisor makes the call."));
}

const a = await tierA();
const b = await tierB();
const cc = await tierC();
const mb = middayBreakStatus();
crossCheck(a);
verdicts(a, mb);

const all = [a.om, a.wttr, ...b, ...cc];
const up = all.filter((r) => r.ok).length;
console.log(c.bold(`\n${up}/${all.length} sources reachable.`));
if (!a.om.ok && !a.wttr.ok) console.log(c.red("BLOCKER: no live weather source. The agent must refuse to confirm conditions."));
console.log("");
