# ElevenLabs agent tool definitions (webhooks)

Create these as **Webhook tools** in the agent's Tools section.
Replace `{BASE_URL}` with the deployed backend URL (HTTPS required).

---

## 1. search_sops

- **Name**: `search_sops`
- **Description**: Search Meridian Construction LLC's company data: SOPs, safety policies, checklists, site rules. Use FIRST for every work or safety question. Empty results mean no company document covers it — refuse and defer, do not invent.
- **Method**: POST
- **URL**: `{BASE_URL}/tools/search_sops`
- **Body parameters**:
  - `query` (string, required): the worker's question, rephrased as a search query.

## 2. check_weather

- **Name**: `check_weather`
- **Description**: Get live wind speed (km/h) and temperature for the Dubai site and a go/no-go verdict against the threshold read from the Meridian Wind & Weather Policy. Use for any question about outside work, scaffolding, cranes, heat, or "what should we do today". Never quote thresholds from memory.
- **Method**: POST
- **URL**: `{BASE_URL}/tools/check_weather`
- **Body parameters**:
  - `activity` (string, required): the activity being asked about, e.g. "working on scaffolding", "crane lift", "handling sheet materials".

## 3. web_lookup

- **Name**: `web_lookup`
- **Description**: Fetch an official guidance page (UAE regulations, official HSE publications, manufacturer documentation) as text when Meridian's company documents do not cover the question. Results rank BELOW company data. Useful start: https://www.mohre.gov.ae or https://www.hse.gov.uk/work-at-height/index.htm
- **Method**: POST
- **URL**: `{BASE_URL}/tools/web_lookup`
- **Body parameters**:
  - `url` (string, required): the page to fetch.
