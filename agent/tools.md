# ElevenLabs agent tool definitions (webhooks)

Create these as **Webhook tools** in the agent's Tools section.
Deployed backend: `https://13.143.65.45.sslip.io` (systemd `heatsafe.service` + Caddy on the VPS).

---

## 1. search_sops

- **Name**: `search_sops`
- **Description**: Search Team 21's company data: SOPs, safety policies, checklists, site rules. Use FIRST for every work or safety question. Empty results mean no company document covers it — say so, then try official guidance via web_lookup before any refusal. Do not invent.
- **Method**: POST
- **URL**: `https://13.143.65.45.sslip.io/tools/search_sops`
- **Body parameters**:
  - `query` (string, required): the worker's question, rephrased as a search query.

## 2. check_weather

- **Name**: `check_weather`
- **Description**: Get live wind speed (km/h) and temperature for the Dubai site and a go/no-go verdict against the threshold read from the Team 21 Wind & Weather Policy. Use for any question about outside work, scaffolding, cranes, heat, or "what should we do today". Never quote thresholds from memory.
- **Method**: POST
- **URL**: `https://13.143.65.45.sslip.io/tools/check_weather`
- **Body parameters**:
  - `activity` (string, required): the activity being asked about, e.g. "working on scaffolding", "crane lift", "handling sheet materials".

## 3. web_search

- **Name**: `web_search`
- **Description**: Search the live web when the company documents do not cover the question. Use IMMEDIATELY after an empty search_sops result, before any refusal. Returns titles, URLs and snippets with official sources (UAE regulators, HSE, OSHA, manufacturers) ranked first — pick one and read it with web_lookup.
- **Method**: POST
- **URL**: `https://13.143.65.45.sslip.io/tools/web_search`
- **Body parameters**:
  - `query` (string, required): the worker's question as a web search query, e.g. "UAE regulations temporary electrical installation construction site".

## 4. web_lookup

- **Name**: `web_lookup`
- **Description**: Fetch an official guidance page (UAE regulations, official HSE publications, manufacturer documentation) as text when Team 21's company documents do not cover the question. Results rank BELOW company data. Useful start: https://www.mohre.gov.ae or https://www.hse.gov.uk/work-at-height/index.htm
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
  "description": "Search the client company's data (Team 21): SOPs, safety policies, checklists, site rules. Use FIRST for every work or safety question. Empty results mean no company document covers it — say so, then try official guidance via web_lookup before any refusal. Do not invent.",
  "api_schema": {
    "url": "https://13.143.65.45.sslip.io/tools/search_sops",
    "method": "POST",
    "path_params_schema": [],
    "query_params_schema": [],
    "request_body_schema": {
      "id": "body",
      "type": "object",
      "description": "Search request over company safety documents.",
      "required": true,
      "value_type": "llm_prompt",
      "properties": [
        {
          "id": "query",
          "type": "string",
          "description": "The worker's question rephrased as a short search query over company safety documents. Keep the key nouns, e.g. \"scaffold pre-use checks\", \"harness inspection\", \"wind limit scaffold work\". Strip filler words.",
          "required": true,
          "value_type": "llm_prompt",
          "dynamic_variable": "",
          "constant_value": "",
          "enum": null
        }
      ]
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
      "id": "body",
      "type": "object",
      "description": "Activity to assess against the weather policy.",
      "required": true,
      "value_type": "llm_prompt",
      "properties": [
        {
          "id": "activity",
          "type": "string",
          "description": "The physical activity the user is asking about, as a short phrase. Examples: \"working on the scaffold\", \"handling sheet materials\", \"crane lift\", \"external work\". If the user asks generally what to work on today, use \"external work\".",
          "required": true,
          "value_type": "llm_prompt",
          "dynamic_variable": "",
          "constant_value": "",
          "enum": null
        }
      ]
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

### web_search

```json
{
  "type": "webhook",
  "name": "web_search",
  "description": "Search the live web when the company documents do not cover the question. Use IMMEDIATELY after an empty search_sops result, before any refusal. Returns titles, URLs and snippets with official sources ranked first — pick the most authoritative and read it with web_lookup. Results rank BELOW company data.",
  "api_schema": {
    "url": "https://13.143.65.45.sslip.io/tools/web_search",
    "method": "POST",
    "path_params_schema": [],
    "query_params_schema": [],
    "request_body_schema": {
      "id": "body",
      "type": "object",
      "description": "Web search request.",
      "required": true,
      "value_type": "llm_prompt",
      "properties": [
        {
          "id": "query",
          "type": "string",
          "description": "The worker's question rephrased as a web search query. Include the jurisdiction when relevant, e.g. \"UAE regulations temporary electrical installation construction site\".",
          "required": true,
          "value_type": "llm_prompt",
          "dynamic_variable": "",
          "constant_value": "",
          "enum": null
        }
      ]
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
  "description": "Fetch an official guidance page (UAE regulations, official HSE publications, manufacturer documentation) as text when the client company's documents do not cover the question. Use it whenever search_sops returns empty, before refusing. Results rank BELOW company data — flag them as \"not company policy\".",
  "api_schema": {
    "url": "https://13.143.65.45.sslip.io/tools/web_lookup",
    "method": "POST",
    "path_params_schema": [],
    "query_params_schema": [],
    "request_body_schema": {
      "id": "body",
      "type": "object",
      "description": "Official guidance page to fetch.",
      "required": true,
      "value_type": "llm_prompt",
      "properties": [
        {
          "id": "url",
          "type": "string",
          "description": "Full HTTPS URL of an official guidance page. Prefer official sources: https://www.hse.gov.uk/work-at-height/index.htm for work-at-height guidance, https://www.mohre.gov.ae for UAE labour rules. Never use random blogs or forums.",
          "required": true,
          "value_type": "llm_prompt",
          "dynamic_variable": "",
          "constant_value": "",
          "enum": null
        }
      ]
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

### language_detection (system tool)

Add via **Add tool → System → Language detection** in the agent's Tools section
(languages themselves are configured in the Agent tab → Additional languages).

```json
{
  "type": "system",
  "name": "language_detection",
  "description": "Switch the conversation language when the worker speaks a complete meaningful phrase in a different supported language, or explicitly asks to switch. Do NOT switch because a tool result or document quote is in English — company documents are English; translate their substance into the conversation language instead. Do not switch on single borrowed words, names, or garbled fragments."
}
```
