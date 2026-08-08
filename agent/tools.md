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

---

## JSON definitions (paste into the tool's JSON editor)

### search_sops

```json
{
  "type": "webhook",
  "name": "search_sops",
  "description": "Search the client company's data (Meridian Construction LLC): SOPs, safety policies, checklists, site rules. Use FIRST for every work or safety question. Empty results mean no company document covers it — refuse and defer, do not invent.",
  "api_schema": {
    "url": "https://13.143.65.45.sslip.io/tools/search_sops",
    "method": "POST",
    "path_params_schema": [],
    "query_params_schema": [],
    "request_body_schema": {
      "type": "object",
      "description": "Search request over company safety documents.",
      "required": ["query"],
      "properties": {
        "query": {
          "type": "string",
          "description": "The worker's question rephrased as a short search query over company safety documents. Keep the key nouns, e.g. \"scaffold pre-use checks\", \"harness inspection\", \"wind limit scaffold work\". Strip filler words."
        }
      }
    },
    "request_headers": [],
    "content_type": "application/json",
    "auth_connection": null
  },
  "response_timeout_secs": 20,
  "dynamic_variables": {
    "dynamic_variable_placeholders": {}
  },
  "assignments": [],
  "interruption_mode": "allow",
  "pre_tool_speech": "auto",
  "tool_call_sound": null,
  "tool_call_sound_behavior": "auto",
  "execution_mode": "immediate",
  "tool_error_handling_mode": "auto",
  "response_mocks": []
}
```

### check_weather

```json
{
  "type": "webhook",
  "name": "check_weather",
  "description": "Get live wind speed and temperature for the configured site (Harbour Point Tower, Dubai Marina) with a go/restricted/no-go verdict against the bands read from the client's weather policy (MER-SOP-021), including heat bands and the UAE summer midday break. Use for any question about outside work, scaffolding, cranes, heat, or \"what should we do today\". Never quote thresholds from memory.",
  "api_schema": {
    "url": "https://13.143.65.45.sslip.io/tools/check_weather",
    "method": "POST",
    "path_params_schema": [],
    "query_params_schema": [],
    "request_body_schema": {
      "type": "object",
      "description": "Activity to assess against the weather policy.",
      "required": ["activity"],
      "properties": {
        "activity": {
          "type": "string",
          "description": "The physical activity the user is asking about, as a short phrase. Examples: \"working on the scaffold\", \"handling sheet materials\", \"crane lift\", \"external work\". If the user asks generally what to work on today, use \"external work\"."
        }
      }
    },
    "request_headers": [],
    "content_type": "application/json",
    "auth_connection": null
  },
  "response_timeout_secs": 60,
  "dynamic_variables": {
    "dynamic_variable_placeholders": {}
  },
  "assignments": [],
  "interruption_mode": "allow",
  "pre_tool_speech": "auto",
  "tool_call_sound": null,
  "tool_call_sound_behavior": "auto",
  "execution_mode": "immediate",
  "tool_error_handling_mode": "auto",
  "response_mocks": []
}
```

### web_lookup

```json
{
  "type": "webhook",
  "name": "web_lookup",
  "description": "Fetch an official guidance page (UAE regulations, official HSE publications, manufacturer documentation) as text when the client company's documents do not cover the question. Results rank BELOW company data — flag them as \"not company policy\".",
  "api_schema": {
    "url": "https://13.143.65.45.sslip.io/tools/web_lookup",
    "method": "POST",
    "path_params_schema": [],
    "query_params_schema": [],
    "request_body_schema": {
      "type": "object",
      "description": "Official guidance page to fetch.",
      "required": ["url"],
      "properties": {
        "url": {
          "type": "string",
          "description": "Full HTTPS URL of an official guidance page. Prefer official sources: https://www.hse.gov.uk/work-at-height/index.htm for work-at-height guidance, https://www.mohre.gov.ae for UAE labour rules. Never use random blogs or forums."
        }
      }
    },
    "request_headers": [],
    "content_type": "application/json",
    "auth_connection": null
  },
  "response_timeout_secs": 60,
  "dynamic_variables": {
    "dynamic_variable_placeholders": {}
  },
  "assignments": [],
  "interruption_mode": "allow",
  "pre_tool_speech": "auto",
  "tool_call_sound": null,
  "tool_call_sound_behavior": "auto",
  "execution_mode": "immediate",
  "tool_error_handling_mode": "auto",
  "response_mocks": []
}
```
