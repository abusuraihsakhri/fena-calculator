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

Fractional Excretion of Sodium (FENa) Calculator

Real implementations for:
- FENa = (UNa × PCr) / (PNa × UCr) × 100
- FEUrea (for patients on diuretics)
- BUN/Creatinine ratio
- Urine osmolality interpretation
- Specific gravity interpretation

References: Miller TR et al. (JAMA 1978), Carvounis CP et al. (Kidney Int 2002)
Stdlib only.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calc_fena()`**: Fractional Excretion of Sodium (FENa).

FENa = (UNa × PCr) / (PNa × UCr) × 100

Interpretation:
    FENa < 1%: Prerenal azotemia (volume depletion, CHF, hepatorenal)
    FENa 1-2%: Indeterminate
    FENa > 2%: Intrinsic renal disease (ATN)

Args:
    urine_na: Urine sodium (mEq/L)
    plasma_cr: Plasma/Serum creatinine (mg/dL)
    plasma_na: Plasma/Serum sodium (mEq/L)
    urine_cr: Urine creatinine (mg/dL)

Returns:
    Dict with FENa percentage and interpretation
- **`calc_feurea()`**: Fractional Excretion of Urea (FEUrea).

FEUrea = (UUrea × PCr) / (PUrea × UCr) × 100

More reliable than FENa in patients on diuretics.

Interpretation:
    FEUrea < 35%: Prerenal azotemia
    FEUrea 35-50%: Indeterminate
    FEUrea > 50%: Intrinsic renal disease (ATN)

Args:
    urine_urea: Urine urea nitrogen (mg/dL)
    plasma_cr: Plasma creatinine (mg/dL)
    plasma_urea: Plasma/BUN (mg/dL)
    urine_cr: Urine creatinine (mg/dL)

Returns:
    Dict with FEUrea percentage and interpretation
- **`calc_bun_cr_ratio()`**: BUN/Creatinine ratio for prerenal vs intrinsic differentiation.

BUN:Cr > 20:1: Prerenal (increased urea reabsorption)
BUN:Cr 15-20:1: Indeterminate
BUN:Cr < 15:1: Intrinsic renal (normal or decreased reabsorption)

Args:
    bun: Blood urea nitrogen (mg/dL)
    creatinine: Serum creatinine (mg/dL)

Returns:
    Dict with BUN/Cr ratio and interpretation
- **`interpret_urine_osmolality()`**: Urine osmolality interpretation for AKI differential.

Prerenal: UOsm > 500 mOsm/kg (concentrated urine)
Intrinsic (ATN): UOsm < 350 mOsm/kg (dilute/isotonic urine)
Normal range: 300-900 mOsm/kg

Also calculates UOsm/SOsm ratio.

Args:
    urine_osmolality: Urine osmolality (mOsm/kg)
    serum_osmolality: Serum osmolality (mOsm/kg)

Returns:
    Dict with interpretation
- **`interpret_specific_gravity()`**: Urine specific gravity interpretation.

Normal: 1.005-1.030
Prerenal: > 1.020 (concentrated)
ATN: ~1.010 (isosthenuria - fixed at plasma SG)

Args:
    sg: Urine specific gravity

Returns:
    Dict with interpretation

---

## 📐 Mathematical Formulation & Logic

```text
  Also calculates UOsm/SOsm ratio.
  p_fena = sub.add_parser("fena", help="Calculate FENa")
  p_feu = sub.add_parser("feurea", help="Calculate FEUrea")
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `id` | Parameter / observation metric | Required |
| `value` | Parameter / observation metric | Required |
| `qty` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t fena-calculator .
docker run -p 8000:8000 fena-calculator
```
