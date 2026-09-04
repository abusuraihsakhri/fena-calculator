import os
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-not-for-production")

import pytest
from fena import (
    calc_fena,
    calc_feurea,
    calc_bun_cr_ratio,
    interpret_urine_osmolality,
    interpret_specific_gravity,
    full_aki_assessment,
    main,
)


# --- FENa ---

def test_fena_prerenal():
    """UNa=10, PCr=2.0, PNa=140, UCr=200 → (10×2)/(140×200)×100 = 0.71%"""
    r = calc_fena(10, 2.0, 140, 200)
    expected = (10 * 2.0) / (140 * 200) * 100  # 0.7143
    assert abs(r["fena_percent"] - expected) < 0.01
    assert r["interpretation"] == "Prerenal azotemia"


def test_fena_intrinsic():
    """UNa=60, PCr=3.0, PNa=140, UCr=40 → (60×3)/(140×40)×100 = 3.21%"""
    r = calc_fena(60, 3.0, 140, 40)
    assert r["fena_percent"] > 2.0
    assert r["interpretation"] == "Intrinsic renal disease (ATN)"


def test_fena_indeterminate():
    """UNa=20, PCr=2.5, PNa=140, UCr=80 → (20×2.5)/(140×80)×100 = 0.45%"""
    # Need to find values that give 1-2%
    # UNa=30, PCr=2.0, PNa=140, UCr=60 → (30×2)/(140×60)×100 = 0.71
    # UNa=50, PCr=2.0, PNa=140, UCr=50 → (50×2)/(140×50)×100 = 1.43
    r = calc_fena(50, 2.0, 140, 50)
    assert 1.0 <= r["fena_percent"] <= 2.0
    assert r["interpretation"] == "Indeterminate"


def test_fena_zero_urine_na():
    """UNa=0 means perfect Na retention = prerenal"""
    r = calc_fena(0, 2.0, 140, 100)
    assert r["fena_percent"] == 0.0
    assert r["interpretation"] == "Prerenal azotemia"


def test_fena_invalid_plasma_na():
    with pytest.raises(ValueError):
        calc_fena(10, 2.0, 0, 100)


def test_fena_invalid_urine_cr():
    with pytest.raises(ValueError):
        calc_fena(10, 2.0, 140, 0)


# --- FEUrea ---

def test_feurea_prerenal():
    """UUrea=500, PCr=2.0, PUrea=60, UCr=200 → (500×2)/(60×200)×100 = 83.3%"""
    # That's actually intrinsic. Let's use values for prerenal
    # UUrea=200, PCr=2.0, PUrea=60, UCr=200 → (200×2)/(60×200)×100 = 3.33%
    # Need < 35%
    # UUrea=100, PCr=2.0, PUrea=40, UCr=100 → (100×2)/(40×100)×100 = 5.0%
    # UUrea=300, PCr=2.0, PUrea=60, UCr=300 → (300×2)/(60×300)×100 = 3.33%
    # Let me try: UUrea=500, PCr=2.0, PUrea=80, UCr=400 → (500×2)/(80×400)×100 = 3.125%
    # Hmm, these are all low. Let me think...
    # FEUrea = (UUrea × PCr) / (PUrea × UCr) × 100
    # For < 35%: UUrea×PCr / (PUrea×UCr) < 0.35
    # UUrea=1000, PCr=2, PUrea=60, UCr=200 → 2000/12000×100 = 16.7% → prerenal
    r = calc_feurea(1000, 2.0, 60, 200)
    assert r["feurea_percent"] < 35
    assert r["interpretation"] == "Prerenal azotemia"


def test_feurea_intrinsic():
    # UUrea=500, PCr=2, PUrea=20, UCr=50 → 1000/1000×100 = 100%
    r = calc_feurea(500, 2.0, 20, 50)
    assert r["feurea_percent"] > 50
    assert r["interpretation"] == "Intrinsic renal disease"


def test_feurea_indeterminate():
    # Need 35-50%
    # UUrea=500, PCr=2, PUrea=40, UCr=70 → 1000/2800×100 = 35.7%
    r = calc_feurea(500, 2.0, 40, 70)
    assert 35 <= r["feurea_percent"] <= 50
    assert r["interpretation"] == "Indeterminate"


# --- BUN/Cr Ratio ---

def test_bun_cr_prerenal():
    r = calc_bun_cr_ratio(60, 2.0)
    assert r["bun_cr_ratio"] == 30.0
    assert r["interpretation"] == "Prerenal pattern"


def test_bun_cr_intrinsic():
    r = calc_bun_cr_ratio(30, 3.0)
    assert r["bun_cr_ratio"] == 10.0
    assert r["interpretation"] == "Intrinsic renal pattern"


def test_bun_cr_indeterminate():
    r = calc_bun_cr_ratio(30, 2.0)
    assert r["bun_cr_ratio"] == 15.0
    assert r["interpretation"] == "Indeterminate"


def test_bun_cr_boundary_20():
    """BUN/Cr = 20 is at boundary; code uses > 20 for prerenal, so 20 is indeterminate."""
    r = calc_bun_cr_ratio(40, 2.0)
    assert r["bun_cr_ratio"] == 20.0
    assert r["interpretation"] == "Indeterminate"


# --- Urine Osmolality ---

def test_urine_osm_prerenal():
    r = interpret_urine_osmolality(600)
    assert "prerenal" in r["interpretation"].lower()


def test_urine_osm_atn():
    r = interpret_urine_osmolality(300)
    assert "intrinsic" in r["interpretation"].lower() or "dilute" in r["interpretation"].lower()


def test_urine_osm_indeterminate():
    r = interpret_urine_osmolality(400)
    assert "isotonic" in r["interpretation"].lower() or "indeterminate" in r["interpretation"].lower()


# --- Specific Gravity ---

def test_sg_prerenal():
    r = interpret_specific_gravity(1.025)
    assert "prerenal" in r["interpretation"].lower() or "concentrated" in r["interpretation"].lower()


def test_sg_atn():
    r = interpret_specific_gravity(1.010)
    assert "isosthenuria" in r["interpretation"].lower() or "intrinsic" in r["interpretation"].lower()


def test_sg_dilute():
    r = interpret_specific_gravity(1.005)
    assert "dilute" in r["interpretation"].lower()


# --- Full Assessment ---

def test_full_assessment_prerenal():
    r = full_aki_assessment(
        urine_na=10, plasma_cr=2.0, plasma_na=140, urine_cr=200, bun=60
    )
    assert "fena" in r
    assert "bun_cr_ratio" in r
    assert "prerenal" in r["overall_assessment"].lower()


def test_full_assessment_with_optional():
    r = full_aki_assessment(
        urine_na=10, plasma_cr=2.0, plasma_na=140, urine_cr=200, bun=60,
        urine_urea=1000, urine_osmolality=600, specific_gravity=1.025
    )
    assert "feurea" in r
    assert "urine_osmolality" in r
    assert "specific_gravity" in r


# --- CLI ---

def test_cli_fena():
    assert main(["fena", "--urine-na", "10", "--plasma-cr", "2.0",
                  "--plasma-na", "140", "--urine-cr", "200"]) == 0


def test_cli_bun_cr():
    assert main(["bun-cr", "--bun", "60", "--cr", "2.0"]) == 0


def test_cli_full():
    assert main(["full", "--urine-na", "10", "--plasma-cr", "2.0",
                  "--plasma-na", "140", "--urine-cr", "200", "--bun", "60"]) == 0
