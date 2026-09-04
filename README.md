# FENA Calculator

> **Domain:** Nephrology & Renal Replacement Protocols
> **Reference Guidelines & Standards:** `KDIGO & KDOQI Clinical Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Fractional Excretion of Sodium (FENa) Calculator for clinical nephrology decision support.

Real implementations for:
- **FENa** = (UNa × PCr) / (PNa × UCr) × 100
- **FEUrea** (for patients on diuretics)
- **BUN/Creatinine ratio**
- **Urine osmolality interpretation**
- **Specific gravity interpretation**
- **Full AKI differential assessment**

References: Miller TR et al. (JAMA 1978), Carvounis CP et al. (Kidney Int 2002)

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calc_fena()`**: Fractional Excretion of Sodium (FENa).
  - FENa < 1%: Prerenal azotemia
  - FENa 1-2%: Indeterminate
  - FENa > 2%: Intrinsic renal disease (ATN)

- **`calc_feurea()`**: Fractional Excretion of Urea (FEUrea).
  - More reliable than FENa in patients on diuretics.
  - FEUrea < 35%: Prerenal azotemia
  - FEUrea 35-50%: Indeterminate
  - FEUrea > 50%: Intrinsic renal disease (ATN)

- **`calc_bun_cr_ratio()`**: BUN/Creatinine ratio for prerenal vs intrinsic differentiation.
  - BUN:Cr > 20:1: Prerenal
  - BUN:Cr 15-20:1: Indeterminate
  - BUN:Cr < 15:1: Intrinsic renal

- **`interpret_urine_osmolality()`**: Urine osmolality interpretation for AKI differential.
  - Prerenal: UOsm > 500 mOsm/kg
  - Intrinsic (ATN): UOsm < 350 mOsm/kg

- **`interpret_specific_gravity()`**: Urine specific gravity interpretation.
  - Prerenal: > 1.020 (concentrated)
  - ATN: ~1.010 (isosthenuria)

- **`full_aki_assessment()`**: Complete AKI differential combining all markers with overall assessment.

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/fena-calculator.git
cd fena-calculator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 CLI Quickstart & Usage

### 1. Calculate FENa
```bash
python cli.py fena --urine-na 10 --plasma-cr 2.0 --plasma-na 140 --urine-cr 200
```

### 2. Calculate FEUrea
```bash
python cli.py feurea --urine-urea 1000 --plasma-cr 2.0 --plasma-bun 60 --urine-cr 200
```

### 3. BUN/Creatinine Ratio
```bash
python cli.py bun-cr --bun 60 --cr 2.0
```

### 4. Urine Osmolality
```bash
python cli.py osmolality --urine-osm 600 --serum-osm 285
```

### 5. Specific Gravity
```bash
python cli.py sg --sg 1.025
```

### 6. Full AKI Assessment
```bash
python cli.py full --urine-na 10 --plasma-cr 2.0 --plasma-na 140 --urine-cr 200 --bun 60
```

### 7. Supervisor Audit
```bash
python cli.py audit --task-id TASK-001 --primary-metric 10.0
```

### 8. Verify Audit Integrity
```bash
python cli.py verify-audit
```

### 9. Start REST API Server
```bash
python cli.py serve --host 0.0.0.0 --port 8000
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude, GPT-4o, and deterministic test mocks.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI REST endpoints and operational Prometheus metrics (`/metrics`).

### Environment Variables

| Variable | Required | Description |
|:---------|:---------|:------------|
| `AUDIT_SECRET_KEY` | Yes | HMAC-SHA256 signing key. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `MODEL_PROVIDER` | No | LLM provider: `mock` (default), `ollama`, `claude`, `openai` |

Copy `.env.example` to `.env` and set your values before running.

---

## 🧪 Testing & Verification

```bash
# Run all tests
pytest -v

# Run specific test files
pytest test_fena.py -v
pytest tests/ -v

# Execute simulation benchmark
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker Compose
cp .env.example .env
# Edit .env and set AUDIT_SECRET_KEY
docker-compose up --build

# Or build and run manually
docker build -t fena-calculator .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key fena-calculator
```

---

## 📁 Project Structure

```
fena-calculator/
├── fena.py                 # Core calculation functions + CLI
├── cli.py                  # CLI entry point (delegates to fena.py)
├── test_fena.py            # Core calculation tests
├── simulator.py            # High-throughput simulation
├── enrichment.py           # Feature enrichment engines
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build
├── docker-compose.yml      # Container orchestration
├── agents/                 # Enterprise agent modules
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic schemas
│   ├── supervisor.py       # Orchestrator
│   ├── workers.py          # Specialized workers
│   ├── api.py              # FastAPI REST server
│   ├── llm_factory.py      # LLM provider factory
│   ├── metrics.py          # Prometheus metrics
│   ├── learning.py         # Bayesian calibration
│   └── streamer.py         # WebSocket telemetry
├── tests/                  # Test suite
│   ├── test_fena_calculator.py
│   └── test_enrichment.py
└── web/                    # Operations console
    └── index.html
```
