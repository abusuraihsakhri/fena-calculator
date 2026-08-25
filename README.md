# FENa Calculator — Fractional Excretion of Sodium

> **Nephrology** — Acute Kidney Injury Differential Diagnosis

## Overview

Real clinical calculator for differentiating prerenal azotemia from intrinsic renal disease using FENa, FEUrea (for diuretic-treated patients), BUN/Creatinine ratio, urine osmolality, and specific gravity.

**References:** Miller TR et al. (JAMA 1978), Carvounis CP et al. (Kidney Int 2002)

## Formulas Implemented

| Calculator | Formula |
|:-----------|:--------|
| **FENa** | (UNa × PCr) / (PNa × UCr) × 100 |
| **FEUrea** | (UUrea × PCr) / (PUrea × UCr) × 100 |
| **BUN/Cr Ratio** | BUN / Creatinine |
| **Urine Osmolality** | UOsm/SOsm ratio interpretation |
| **Specific Gravity** | SG interpretation for AKI differential |

## CLI Usage

```bash
# FENa
python fena.py fena --urine-na 20 --plasma-cr 2.5 --plasma-na 140 --urine-cr 80

# FEUrea (for patients on diuretics)
python fena.py feurea --urine-urea 500 --plasma-cr 2.5 --plasma-bun 40 --urine-cr 80

# BUN/Creatinine ratio
python fena.py bun-cr --bun 60 --cr 2.0

# Urine osmolality
python fena.py osmolality --urine-osm 350

# Specific gravity
python fena.py sg --sg 1.010

# Full AKI assessment
python fena.py full --urine-na 20 --plasma-cr 2.5 --plasma-na 140 --urine-cr 80 --bun 60
```

## Python API

```python
from fena import calc_fena, calc_feurea, calc_bun_cr_ratio, full_aki_assessment

# FENa
result = calc_fena(urine_na=20, plasma_cr=2.5, plasma_na=140, urine_cr=80)
print(result["fena_percent"])  # 7.14
print(result["interpretation"])  # "Intrinsic renal disease (ATN)"

# Full assessment
full = full_aki_assessment(urine_na=10, plasma_cr=2.0, plasma_na=140,
                            urine_cr=100, bun=60)
print(full["overall_assessment"])
```

## Interpretation Guide

| Marker | Prerenal | Intrinsic (ATN) |
|:-------|:---------|:----------------|
| FENa | < 1% | > 2% |
| FEUrea | < 35% | > 50% |
| BUN:Cr | > 20:1 | < 15:1 |
| UOsm | > 500 | < 350 |
| SG | > 1.020 | ~1.010 |

## License

MIT License.
