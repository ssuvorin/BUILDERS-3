# ElevenLabs agent tool definitions (webhooks)

Create these as **Webhook tools** in the agent's Tools section.
Deployed backend: `https://13.143.65.45.sslip.io` (systemd `heatsafe.service` + Caddy on the VPS).

---

## 1. search_sops

- **Name**: `search_sops`
- **Description**: Search Meridian Construction LLC's company data: SOPs, safety policies, checklists, site rules. Use FIRST for every work or safety question. Empty results mean no company document covers it — refuse and defer, do not invent.
- **Method**: POST
- **URL**: `https://13.143.65.45.sslip.io/tools/search_sops`
- **Body parameters**:
  - `query` (string, required): the worker's question, rephrased as a search query.

## 2. check_weather

- **Name**: `check_weather`
- **Description**: Get live wind speed (km/h) and temperature for the Dubai site and a go/no-go verdict against the threshold read from the Meridian Wind & Weather Policy. Use for any question about outside work, scaffolding, cranes, heat, or "what should we do today". Never quote thresholds from memory.
- **Method**: POST
- **URL**: `https://13.143.65.45.sslip.io/tools/check_weather`
- **Body parameters**:
  - `activity` (string, required): the activity being asked about, e.g. "working on scaffolding", "crane lift", "handling sheet materials".

## 3. web_lookup

- **Name**: `web_lookup`
- **Description**: Fetch an official guidance page (UAE regulations, official HSE publications, manufacturer documentation) as text when Meridian's company documents do not cover the question. Results rank BELOW company data. Useful start: https://www.mohre.gov.ae or https://www.hse.gov.uk/work-at-height/index.htm
- **Method**: POST
- **URL**: `https://13.143.65.45.sslip.io/tools/web_lookup`
- **Body parameters**:
  - `url` (string, required): the page to fetch.
