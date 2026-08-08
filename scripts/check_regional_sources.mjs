#!/usr/bin/env node
/**
 * Global regulatory source probe — HeatSafe worldwide expansion
 *
 * The UAE is the launch market, not the product. This probes the official
 * occupational-safety authority for every market we'd plausibly sell into, so the
 * regional tier of the source register is a verified list rather than a guess.
 *
 *   node scripts/check_regional_sources.mjs
 *
 * No API keys, no dependencies. Node 18+.
 */

const TIMEOUT_MS = 15000;
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36";

const c = {
  green: (s) => `\x1b[32m${s}\x1b[0m`, red: (s) => `\x1b[31m${s}\x1b[0m`,
  yellow: (s) => `\x1b[33m${s}\x1b[0m`, dim: (s) => `\x1b[2m${s}\x1b[0m`, bold: (s) => `\x1b[1m${s}\x1b[0m`,
};

// region, authority, what it governs, url
const SOURCES = [
  ["GCC",       "UAE MOHRE",              "Midday break, labour law",            "https://www.mohre.gov.ae/en/guidance-and-awareness-portal-new/the-midday-break"],
  ["GCC",       "UAE u.ae",               "Govt portal, H&S at workplace",       "https://u.ae/en/information-and-services/jobs/health-and-safety-at-workplace"],
  ["GCC",       "UAE NCM",                "Met authority, storm warnings",       "https://www.ncm.gov.ae/?lang=en"],
  ["GCC",       "Dubai Municipality",     "Construction safety practice",        "https://www.dm.gov.ae/"],
  ["GCC",       "Saudi HRSD",             "Labour law, summer work ban",         "https://www.hrsd.gov.sa/en"],
  ["GCC",       "Qatar Ministry of Labour","Summer working hours ban",           "https://www.mol.gov.qa/en/"],
  ["UK",        "HSE",                    "Work at height, construction",        "https://www.hse.gov.uk/work-at-height/index.htm"],
  ["UK",        "legislation.gov.uk",     "Work at Height Regs 2005",            "https://www.legislation.gov.uk/uksi/2005/735/contents/made"],
  ["UK",        "NASC",                   "Scaffolding industry standards",      "https://nasc.org.uk/"],
  ["UK",        "Met Office",             "National met service",                "https://www.metoffice.gov.uk/"],
  ["EU",        "EU-OSHA",                "EU OSH agency",                       "https://osha.europa.eu/en"],
  ["EU",        "EUR-Lex 92/57/EEC",      "Construction sites directive",        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A31992L0057"],
  ["EU",        "EUR-Lex 89/391/EEC",     "OSH framework directive",             "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A31989L0391"],
  ["US",        "OSHA",                   "Federal OSH standards",               "https://www.osha.gov/laws-regs/regulations/standardnumber/1926"],
  ["US",        "OSHA heat",              "Heat illness prevention",             "https://www.osha.gov/heat"],
  ["US",        "NIOSH",                  "Heat stress criteria",                "https://www.cdc.gov/niosh/topics/heatstress/"],
  ["US",        "NWS",                    "National weather service",            "https://www.weather.gov/"],
  ["Canada",    "CCOHS",                  "OHS guidance",                        "https://www.ccohs.ca/"],
  ["Australia", "Safe Work Australia",    "Model WHS laws",                      "https://www.safeworkaustralia.gov.au/"],
  ["Australia", "SafeWork NSW",           "State regulator",                     "https://www.safework.nsw.gov.au/"],
  ["Australia", "BOM",                    "Bureau of Meteorology",               "http://www.bom.gov.au/"],
  ["Singapore", "MOM",                    "WSH Act, heat stress advisory",       "https://www.mom.gov.sg/workplace-safety-and-health"],
  ["India",     "DGFASLI",                "Factory & labour safety",             "https://dgfasli.gov.in/"],
  ["India",     "IMD",                    "Met dept, heat warnings",             "https://mausam.imd.gov.in/"],
  ["Brazil",    "Gov.br NR-35",           "Work at height standard",             "https://www.gov.br/trabalho-e-emprego/pt-br"],
  ["S. Africa", "Dept Employment&Labour", "Construction Regulations",            "https://www.labour.gov.za/"],
  ["Japan",     "MHLW",                   "Industrial safety & health",          "https://www.mhlw.go.jp/english/"],
  ["Global",    "ILO",                    "C167 construction convention",        "https://www.ilo.org/international-labour-standards"],
  ["Global",    "ISO 45001",              "OHS management standard",             "https://www.iso.org/standard/63787.html"],
  ["Global",    "WMO",                    "World Meteorological Org",            "https://wmo.int/"],
  ["Global",    "Open-Meteo",             "Worldwide weather, no key",           "https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&current=temperature_2m"],
];

async function probe(url) {
  const started = Date.now();
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, { signal: ctrl.signal, redirect: "follow", headers: { "User-Agent": UA } });
    return { ok: res.ok, status: res.status, ms: Date.now() - started };
  } catch (err) {
    return { ok: false, status: err.name === "AbortError" ? "timeout" : "unreachable", ms: Date.now() - started };
  } finally { clearTimeout(t); }
}

console.log(c.bold("\nGlobal regulatory source probe\n"));
console.log(c.dim("  The UAE is the launch market. This checks the authority we'd cite in each"));
console.log(c.dim("  market we could sell into. A source that is reachable and public can be read"));
console.log(c.dim("  by context.dev; one that isn't needs a licensed feed or a local partner.\n"));

const results = [];
let region = "";
for (const [reg, authority, governs, url] of SOURCES) {
  if (reg !== region) { region = reg; console.log(c.bold(`\n  ${reg}`)); }
  const r = await probe(url);
  const badge = r.ok ? c.green(" UP ") : c.red("DOWN");
  console.log(`   ${badge} ${authority.padEnd(26)} ${c.dim(governs.padEnd(34))} ${r.ok ? c.dim(r.ms + "ms") : c.red(String(r.status))}`);
  results.push({ region: reg, authority, ok: r.ok });
}

const up = results.filter((r) => r.ok).length;
console.log(c.bold(`\n\n  ${up}/${results.length} reachable.\n`));

const byRegion = {};
for (const r of results) {
  byRegion[r.region] ||= { up: 0, total: 0 };
  byRegion[r.region].total++;
  if (r.ok) byRegion[r.region].up++;
}
console.log(c.dim("  Coverage by market:"));
for (const [reg, s] of Object.entries(byRegion)) {
  const full = s.up === s.total;
  console.log(`   ${full ? c.green("✓") : c.yellow("!")} ${reg.padEnd(11)} ${s.up}/${s.total}`);
}
console.log("");
