# Agent Viper — AI-Assisted Pentesting Platform

An agentic security platform that orchestrates a LangGraph pipeline of specialized
LangChain agents to perform web-application penetration-testing analysis.

**Audience / owner:** DHL ITS Infosec Services penetration-testing team.

> **Advisory only.** Every artifact the platform produces — test cases, severity,
> payloads, gap reports, attack chains, remediation, critical advisories — is a
> recommendation. **No payload is ever executed automatically.** The tester reviews
> and confirms every output before it enters the engagement record.

---

## What the platform does

| Capability | Output |
|---|---|
| **Source-to-runtime mapping** | Translates a SAST finding (file + line) into the live endpoint, method, parameters, headers, and auth context to test. |
| **Coverage expansion** | Each finding seeds 2–4 additional test cases on *other* endpoints sharing the same pattern — not just one test per bug. |
| **Burp-Repeater-ready test cases** | Endpoint, method, headers, body, raw HTTP request **and** a curl command, per case. Pasteable straight into Burp Suite Repeater. |
| **Gap analysis** | Full attack-surface map vs. ingested findings; tech-stack-specific gaps; prioritized. |
| **Attack-chain analysis** | Multi-step chains with component findings, sequence, business impact, verification steps. |
| **Red Team Advisor** | Final pass that shortlists only the issues that plausibly chain to RCE / full compromise, with breach narrative, impact, and per-advisory remediation. |
| **Severity classification** | Critical / High / Medium / Low via contextual reasoning, not raw CVSS — flags severity elevation when findings compose. |
| **Knowledge-base enrichment** | CISA KEV mirror + a curated compromise-recipe playbook (Log4Shell, Spring4Shell, ProxyShell, Confluence OGNL, Struts2, etc.) consulted offline. |

---

## Quick Start (DEV — Windows)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama with `qwen2.5-coder:7b` (`ollama pull qwen2.5-coder:7b`)

> No Redis, no Celery, no WSL. The scan pipeline runs in-process via daemon threads.

### Setup

```powershell
# 1 — Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Copy env file (uses the seeded admin account)
copy ..\config\.env.dev .env.dev

# Init DB and seed mock data
python scripts/init_db.py
python scripts/seed_mock_data.py

# 2 — Frontend
cd ..\frontend
npm install
```

### Run (2 terminals)

```powershell
# Terminal 1 — Backend API
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Or use `.\start.ps1` from the repo root to launch both.

### URLs
| Service   | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:3000        |
| Swagger   | http://localhost:8000/swagger |
| ReDoc     | http://localhost:8000/redoc  |
| Health    | http://localhost:8000/health |

### Login (DEV)
```
Username: admin@agentviper.local
Password: Harbor-Quartz-Meadow-58
```
First login forces a password change. Account lockout, bcrypt_sha256, and a
configurable password policy are enabled (`core/password_policy.py`).

---

## Architecture

The live LangGraph `StateGraph` (`backend/graph/pipeline.py`) is **6 core agents**
plus an **optional 2-agent Burp branch** that runs only when a `target_url` is set
and Burp is reachable (or in mock mode):

```
guardian → harvester ─┬─(Burp + target_url)→ striker → decoder ─┐
                      └─(otherwise, skip)──────────────────────────┴→ analyst
        → test_case_builder → attack_chain_builder → redteam → END
```

| Agent (codename → technical name) | Type | Role |
|---|---|---|
| `guardian`            → **PREREQ_CHECKER**        | Automation | Eight pre-flight checks (env, DB, LLM, optional Burp — Burp check is advisory). |
| `harvester`           → **INPUT_LOADER**          | Automation | Ingests SAST/DAST/enum/recon JSON via LangChain `JSONLoader`. |
| `striker`             → **BURP_SCANNER** *(opt)*  | Automation | Triggers a live Burp scan via LangChain `@tool` (mock mode supported). |
| `decoder`             → **SCAN_PARSER** *(opt)*   | LLM (LCEL) | Parses Burp results and merges them into `raw_dast`. |
| `analyst`             → **RUNTIME_MAPPER**        | LLM (LCEL) | Attack-surface mapping; SAST → live-endpoint translation with explicit `runtime_manifestation`. |
| `test_case_builder`   → **TESTCASE_GENERATOR**    | LLM (LCEL) | Burp-Repeater-ready test cases incl. raw HTTP + curl + coverage expansion (~50% on adjacent endpoints). |
| `attack_chain_builder`→ **ATTACK_CHAIN_BUILDER**  | LLM (LCEL) | Multi-step attack chains across findings. |
| `redteam`             → **RED_TEAM_ADVISOR**      | LLM (LCEL) | Final breach-path shortlist (RCE / full compromise only), enriched by CISA KEV + recipe playbook. |

> File and function identifiers still use the original codenames (`guardian_node`,
> `harvester_node`, …). Only logs, docstrings, and human-facing labels use the
> technical names above. Legacy agent files exist on disk (`nexus.py`, `herald.py`,
> `seeker.py`, `mapper.py`, `chainmaker.py`, `architect.py`, `inspector.py`,
> `courier.py`, `command_generator.py`) but are **not** wired into the graph; they
> remain importable for ad-hoc `/agents/{name}/run` experiments.

### Two-phase input
1. **AI Scout reconnaissance** — structured intelligence package (scope, endpoints,
   methods, parameters, ports, tech stack) feeds in as primary input.
2. **SAST / DAST / manual reports** — JSON documents ingested by `harvester`; an
   optional live Burp scan merges into the same `raw_dast` bucket.

### Storage model (highlights)
- **`test_cases`** — denormalised: each case has its own `http_request`,
  `curl_command`, `patched_response`, `parameter`, `confidence`, `auth_required`,
  `source_finding`, and `remediation` columns.
- **`critical_advisories`** — exploitation reasoning (`compromise_narrative`,
  `impact`) lives in separate columns from the dedicated `remediation` column.
- **`agent_cache`** — content-addressed (`<agent>:<sha256(inputs)>`), **shared across
  scans**. Identical inputs reuse prior LLM output to cut token spend. Bypass with
  `force_refresh=true` on `/agents/{name}/run`.
- **`agent_traces`** — per-agent prompts, responses, tool calls, reasoning, and
  timings powering the step-through debugging UI.

---

## Individual Agent API

Every agent is triggerable independently:

```http
POST /agents/{agent_name}/run
{ "scan_id": "uuid" }                           ← run against an existing checkpoint
{ "raw_input": {...} }                          ← standalone test with raw data
{ "scan_id": "uuid", "force_refresh": true }    ← bypass agent_cache
```

Full schema at <http://localhost:8000/swagger>.

---

## Knowledge Bases (offline, no runtime network)

- **`services/kev/`** — CISA Known Exploited Vulnerabilities mirror. Refresh with
  `python scripts/refresh_kev.py`; `services.kev.reset_index()` makes the next
  scan pick up new data without a restart.
- **`services/recipes/`** — 17-recipe compromise playbook (`data/recipes.yaml`):
  Log4Shell, Spring4Shell, ProxyShell, Confluence OGNL, Struts2, Tomcat Ghostcat,
  Apache 2.4.49 traversal, Jenkins Groovy console, Spring Actuator env,
  Drupalgeddon2, phpMyAdmin default, WordPress xmlrpc, GitLab ExifTool, plus
  generic file-upload / SQLi-to-RCE / deserialization / SSRF-metadata patterns.
  Adding more is a data-file edit, not code.

### Knowledge Base Checklist

- Verify source freshness before a release (`kev`, `cve`, `recipes`, `nuclei`, `owasp`).
- Refresh datasets with scripts (`refresh_kev.py`, `refresh_nvd.py`) or Admin KB refresh endpoint.
- Confirm indexes reload successfully (no startup/runtime parse errors in backend logs).
- Validate at least one scan uses the updated KB content (new CVE/KEV/recipe appears in results).
- Record refresh timestamp and operator in release notes or operations log.
- If refresh fails, keep prior snapshot and roll back to last known-good dataset.

---

## LangChain Stack

| Component              | Usage                                          |
|------------------------|------------------------------------------------|
| LangGraph `StateGraph` | Pipeline + pause/resume (PostgreSQL checkpointer) |
| LCEL chains            | `prompt | llm | parser` on every LLM agent     |
| `ChatOllama` / Anthropic | LLM backends with `with_fallbacks()`         |
| `JsonOutputParser`     | Structured JSON from every LLM agent           |
| `BaseCallbackHandler`  | Auto token / cost / latency capture            |
| `@tool` decorator      | `striker` (Burp) as a LangChain tool           |
| `JSONLoader`           | `harvester` document ingestion                 |

LLM strategy: local Ollama (`qwen2.5-coder:7b`) in DEV — zero per-token cost;
pluggable to Anthropic / OpenAI for PROD via `services/llm/factory.py`.

---

## Security Standards
- JWT in memory only — never `localStorage`
- bcrypt_sha256, account lockout, password policy, `/auth/change-password`
- SQLAlchemy ORM only (no raw SQL)
- Pydantic v2 validation on all inputs
- Path-traversal prevention on all file ops
- Prompt-injection sanitization before every LLM call
- PII and credential scanning on all outputs
- Rate limiting: 5/min login, 10/hr scan execute
- Security headers on every response

---

## Known Gaps vs. Original Spec

Pre-identified scope candidates — these are the value-prop differentiators in
the original spec, in priority order:

1. **Dedicated Payload Advisor agent** — per-vuln-class payload sets tailored to
   the detected stack. Today payloads only appear as a field inside test cases.
2. **Dedicated Tester Guidance agent** — "what to observe / how to validate /
   what counts as confirmed exploitation" beyond remediation.
3. **Finding Correlation Report** — explicit SAST ↔ DAST ↔ manual correlation
   document (the data exists; the document does not).
4. **SharePoint delivery** — outputs are written to `settings.OUTPUT_PATH` only;
   PROD ingestion + delivery to the SharePoint document library is unimplemented.

