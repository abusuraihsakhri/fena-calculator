# FENa Calculator

### [Open the Live Application →](https://abusuraihsakhri.github.io/fena-calculator/)

An educational nephrology calculator for fractional excretion of sodium (FENa), fractional excretion of urea (FEUrea), and supporting urinary indices. A browser application and Python CLI use the same standard arithmetic expressions; the browser version needs no Python runtime or server.

## Browser application

Open the application at **web/index.html** through a local static HTTP server, or start the included FastAPI server and visit http://localhost:8000/. Static hosting is supported through GitHub Pages. It accepts serum and urine sodium/creatinine measurements, with optional BUN, urine urea nitrogen, urine osmolality, and urine specific gravity.

Enter laboratory values and select **Calculate indices**. Optional measurements reveal the corresponding additional results. **Copy summary** copies the displayed interpretations. **Reset** clears the calculation output and restores the default example inputs.

**Privacy:** The static browser calculator performs all computations locally and does not submit results or inputs to a backend, analytics service, or browser storage. Do not enter identifiable patient information. The separate REST demonstration endpoints, when deployed, process requests on their server and may retain limited task metadata in process memory.

## Equations and interpretation

| Index | Formula | Conventional ranges |
|---|---|---|
| FENa (%) | (urine Na × serum creatinine) / (serum Na × urine creatinine) × 100 | <1% prerenal pattern; 1–2% indeterminate; >2% intrinsic pattern |
| FEUrea (%) | (urine urea nitrogen × serum creatinine) / (BUN × urine creatinine) × 100 | <35% prerenal pattern; 35–50% indeterminate; >50% intrinsic pattern |
| BUN:creatinine | BUN / serum creatinine | <15 intrinsic pattern; 15–20 indeterminate; >20 prerenal pattern |

Urine osmolality and specific gravity are also interpreted using conventional concentration ranges. Sodium measurements must share units; serum and urine creatinine must share units; urea results must both represent urea nitrogen (not mixed urea versus urea nitrogen). The interface uses mEq/L for sodium and mg/dL for creatinine and urea nitrogen.

**Clinical limitations:** These historical thresholds are patterns, not a validated AKI diagnostic algorithm. Diuretic exposure, CKD, sepsis, non-oliguric AKI, obstruction, and glomerular disease can limit discrimination. FEUrea is not universally reliable in diuretic-treated patients. Interpret alongside clinical examination, medications, urine sediment, clinical course, and other investigations. Do not use this tool as a standalone basis for therapy.

## Local development and tests

Python 3.10–3.12 is tested in CI. Node.js 22 is used for independent browser-calculation tests.

~~~bash
git clone https://github.com/abusuraihsakhri/fena-calculator.git
cd fena-calculator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# The in-memory audit component requires a server-side HMAC key:
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

python cli.py fena --urine-na 10 --plasma-cr 2 --plasma-na 140 --urine-cr 200
python cli.py feurea --urine-urea 1000 --plasma-cr 2 --plasma-bun 60 --urine-cr 200
python cli.py full --urine-na 10 --plasma-cr 2 --plasma-na 140 --urine-cr 200 --bun 60
python cli.py serve --host 127.0.0.1 --port 8000

python -m pytest -q
node --test tests/test_browser.mjs
~~~

For standalone static preview: run **python -m http.server 8080** and navigate to http://localhost:8080/web/. No dependency download or build step is needed for the browser app.

## REST demonstration API and task-audit modules

FastAPI exposes /health, /metrics (JSON counts), /api/audit, /api/chat, /api/audit/logs, and API documentation at /docs. The chat endpoint uses a deterministic mock; non-mock external LLM providers are not implemented. The task supervisor uses illustrative thresholds **not validated for clinical decision-making**.

Audit entries are signed with an HMAC-SHA256 chain in **process memory**; this is not a persistent or independently anchored audit trail. Set AUDIT_SECRET_KEY to a random server-side secret. Reading /api/audit/logs requires a separate AUDIT_READ_TOKEN environment variable and matching X-Audit-Read-Token header (access is disabled if the token is absent). The regex identifier filter is limited and does not guarantee de-identification, HIPAA compliance, or complete PHI detection. Do not deploy these demonstration endpoints to accept real patient data.

Docker users can configure AUDIT_SECRET_KEY in a private .env file and run **docker compose up --build**. Never commit secrets. .env.example shows the variables.

## Deployment and compatibility

Static browser code is in **web/** (HTML, CSS, native JavaScript modules). The GitHub Pages workflow publishes that folder when Pages is configured to use GitHub Actions. A root index.html redirects to web/ for branch-root hosting.

Modern desktop and mobile browsers supporting ES modules are required. The browser implementation uses JavaScript rather than Pyodide because no third-party Python packages are needed for calculations. The Python CLI and FastAPI server remain separate.

## License

[MIT](LICENSE).
