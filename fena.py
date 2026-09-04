#!/usr/bin/env python3
"""
Fractional Excretion of Sodium (FENa) Calculator

Real implementations for:
- FENa = (UNa × PCr) / (PNa × UCr) × 100
- FEUrea (for patients on diuretics)
- BUN/Creatinine ratio
- Urine osmolality interpretation
- Specific gravity interpretation

References: Miller TR et al. (JAMA 1978), Carvounis CP et al. (Kidney Int 2002)
Stdlib only.
"""

import argparse
import json
import sys
from typing import Dict, Any

from agents.base import AuditLogger, PHIGuard, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


def calc_fena(urine_na: float, plasma_cr: float, plasma_na: float,
              urine_cr: float) -> Dict[str, Any]:
    """
    Fractional Excretion of Sodium (FENa).

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
    """
    if plasma_na <= 0:
        raise ValueError("Plasma sodium must be positive")
    if urine_cr <= 0:
        raise ValueError("Urine creatinine must be positive")
    if plasma_cr <= 0:
        raise ValueError("Plasma creatinine must be positive")
    if urine_na < 0:
        raise ValueError("Urine sodium cannot be negative")

    fena = (urine_na * plasma_cr) / (plasma_na * urine_cr) * 100.0

    if fena < 1.0:
        interpretation = "Prerenal azotemia"
        etiology = ["Volume depletion/dehydration", "Congestive heart failure",
                     "Hepatorenal syndrome", "Cardiorenal syndrome",
                     "NSAIDs, ACE inhibitors, ARBs"]
        recommendation = "Likely prerenal. Assess volume status, consider fluid challenge."
    elif fena <= 2.0:
        interpretation = "Indeterminate"
        etiology = ["Mixed prerenal/intrinsic", "Early ATN",
                     "Post-obstructive nephropathy", "Rhabdomyolysis",
                     "Contrast nephropathy", "Sepsis with early AKI"]
        recommendation = "Indeterminate zone. Correlate with clinical context and other biomarkers."
    else:
        interpretation = "Intrinsic renal disease (ATN)"
        etiology = ["Acute tubular necrosis (ATN)", "Acute interstitial nephritis (AIN)",
                     "Aminoglycoside nephrotoxicity", "Myoglobinuria"]
        recommendation = "Likely intrinsic renal disease. Evaluate for ATN causes, review nephrotoxins."

    return {
        "fena_percent": round(fena, 2),
        "interpretation": interpretation,
        "possible_etiology": etiology,
        "recommendation": recommendation,
        "inputs": {
            "urine_na_meq_l": urine_na,
            "plasma_cr_mg_dl": plasma_cr,
            "plasma_na_meq_l": plasma_na,
            "urine_cr_mg_dl": urine_cr,
        },
        "note": ("FENa may be unreliable in patients on diuretics, "
                 "with CKD, or with contrast nephropathy. Use FEUrea in diuretic-treated patients."),
    }


def calc_feurea(urine_urea: float, plasma_cr: float,
                plasma_urea: float, urine_cr: float) -> Dict[str, Any]:
    """
    Fractional Excretion of Urea (FEUrea).

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
    """
    if plasma_urea <= 0:
        raise ValueError("Plasma BUN must be positive")
    if urine_cr <= 0:
        raise ValueError("Urine creatinine must be positive")
    if plasma_cr <= 0:
        raise ValueError("Plasma creatinine must be positive")
    if urine_urea < 0:
        raise ValueError("Urine urea cannot be negative")

    feurea = (urine_urea * plasma_cr) / (plasma_urea * urine_cr) * 100.0

    if feurea < 35.0:
        interpretation = "Prerenal azotemia"
        recommendation = "Prerenal pattern. Assess volume status."
    elif feurea <= 50.0:
        interpretation = "Indeterminate"
        recommendation = "Indeterminate. Correlate clinically."
    else:
        interpretation = "Intrinsic renal disease"
        recommendation = "Intrinsic renal pattern. Evaluate for ATN."

    return {
        "feurea_percent": round(feurea, 2),
        "interpretation": interpretation,
        "recommendation": recommendation,
        "inputs": {
            "urine_urea_mg_dl": urine_urea,
            "plasma_cr_mg_dl": plasma_cr,
            "plasma_bun_mg_dl": plasma_urea,
            "urine_cr_mg_dl": urine_cr,
        },
        "note": "FEUrea is preferred over FENa in patients receiving diuretics.",
    }


def calc_bun_cr_ratio(bun: float, creatinine: float) -> Dict[str, Any]:
    """
    BUN/Creatinine ratio for prerenal vs intrinsic differentiation.

    BUN:Cr > 20:1: Prerenal (increased urea reabsorption)
    BUN:Cr 15-20:1: Indeterminate
    BUN:Cr < 15:1: Intrinsic renal (normal or decreased reabsorption)

    Args:
        bun: Blood urea nitrogen (mg/dL)
        creatinine: Serum creatinine (mg/dL)

    Returns:
        Dict with BUN/Cr ratio and interpretation
    """
    if creatinine <= 0:
        raise ValueError("Creatinine must be positive")
    if bun < 0:
        raise ValueError("BUN cannot be negative")

    ratio = bun / creatinine

    if ratio > 20:
        interpretation = "Prerenal pattern"
        etiology = ["Volume depletion", "GI bleeding", "High protein diet/catabolic state",
                     "Corticosteroid use", "Tetracycline"]
        recommendation = "Elevated BUN:Cr ratio suggests prerenal etiology or increased urea production."
    elif ratio >= 15:
        interpretation = "Indeterminate"
        etiology = ["Mixed picture"]
        recommendation = "Borderline ratio. Correlate with other clinical data."
    else:
        interpretation = "Intrinsic renal pattern"
        etiology = ["Acute tubular necrosis", "Liver disease (decreased urea synthesis)",
                     "Low protein diet", "Malnutrition", "Rhabdomyolysis"]
        recommendation = "Low BUN:Cr ratio may indicate intrinsic renal disease or decreased urea production."

    return {
        "bun_cr_ratio": round(ratio, 1),
        "bun": bun,
        "creatinine": creatinine,
        "interpretation": interpretation,
        "possible_etiology": etiology,
        "recommendation": recommendation,
    }


def interpret_urine_osmolality(urine_osmolality: float,
                                serum_osmolality: float = 285.0) -> Dict[str, Any]:
    """
    Urine osmolality interpretation for AKI differential.

    Prerenal: UOsm > 500 mOsm/kg (concentrated urine)
    Intrinsic (ATN): UOsm < 350 mOsm/kg (dilute/isotonic urine)
    Normal range: 300-900 mOsm/kg

    Also calculates UOsm/SOsm ratio.

    Args:
        urine_osmolality: Urine osmolality (mOsm/kg)
        serum_osmolality: Serum osmolality (mOsm/kg)

    Returns:
        Dict with interpretation
    """
    if serum_osmolality <= 0:
        raise ValueError("Serum osmolality must be positive")

    ratio = urine_osmolality / serum_osmolality

    if urine_osmolality > 500:
        interpretation = "Concentrated urine (prerenal pattern)"
        recommendation = "Urine is concentrated, consistent with prerenal azotemia."
    elif urine_osmolality >= 350:
        interpretation = "Isotonic urine (indeterminate)"
        recommendation = "Isotonic urine. May be early ATN or mixed picture."
    else:
        interpretation = "Dilute urine (intrinsic renal pattern)"
        recommendation = "Dilute urine consistent with ATN (impaired concentrating ability)."

    return {
        "urine_osmolality": urine_osmolality,
        "serum_osmolality": serum_osmolality,
        "u_osm_s_osm_ratio": round(ratio, 2),
        "interpretation": interpretation,
        "recommendation": recommendation,
    }


def interpret_specific_gravity(sg: float) -> Dict[str, Any]:
    """
    Urine specific gravity interpretation.

    Normal: 1.005-1.030
    Prerenal: > 1.020 (concentrated)
    ATN: ~1.010 (isosthenuria - fixed at plasma SG)

    Args:
        sg: Urine specific gravity

    Returns:
        Dict with interpretation
    """
    if sg < 1.000:
        raise ValueError("Specific gravity must be ≥ 1.000")

    if sg > 1.020:
        interpretation = "Concentrated urine (prerenal pattern)"
        recommendation = "High SG suggests intact tubular function, consistent with prerenal."
    elif sg >= 1.010:
        interpretation = "Isosthenuria (intrinsic renal pattern)"
        recommendation = "SG ~1.010 suggests impaired concentrating ability (ATN)."
    else:
        interpretation = "Dilute urine"
        recommendation = "Very dilute urine. Consider diabetes insipidus or excessive fluid intake."

    return {
        "specific_gravity": sg,
        "interpretation": interpretation,
        "recommendation": recommendation,
    }


def full_aki_assessment(urine_na: float, plasma_cr: float, plasma_na: float,
                         urine_cr: float, bun: float,
                         urine_urea: float = None,
                         urine_osmolality: float = None,
                         serum_osmolality: float = 285.0,
                         specific_gravity: float = None) -> Dict[str, Any]:
    """
    Complete AKI differential assessment combining all markers.
    """
    result = {
        "fena": calc_fena(urine_na, plasma_cr, plasma_na, urine_cr),
        "bun_cr_ratio": calc_bun_cr_ratio(bun, plasma_cr),
    }

    if urine_urea is not None:
        result["feurea"] = calc_feurea(urine_urea, plasma_cr, bun, urine_cr)

    if urine_osmolality is not None:
        result["urine_osmolality"] = interpret_urine_osmolality(urine_osmolality, serum_osmolality)

    if specific_gravity is not None:
        result["specific_gravity"] = interpret_specific_gravity(specific_gravity)

    # Overall assessment
    fena_val = result["fena"]["fena_percent"]
    bun_ratio = result["bun_cr_ratio"]["bun_cr_ratio"]

    prerenal_signals = 0
    intrinsic_signals = 0

    if fena_val < 1:
        prerenal_signals += 1
    elif fena_val > 2:
        intrinsic_signals += 1

    if bun_ratio > 20:
        prerenal_signals += 1
    elif bun_ratio < 15:
        intrinsic_signals += 1

    if "feurea" in result:
        feurea_val = result["feurea"]["feurea_percent"]
        if feurea_val < 35:
            prerenal_signals += 1
        elif feurea_val > 50:
            intrinsic_signals += 1

    if prerenal_signals > intrinsic_signals:
        result["overall_assessment"] = "Prerenal azotemia (most likely)"
    elif intrinsic_signals > prerenal_signals:
        result["overall_assessment"] = "Intrinsic renal disease (most likely)"
    else:
        result["overall_assessment"] = "Indeterminate - further evaluation needed"

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="fena-calculator",
        description="Fractional Excretion of Sodium (FENa) Calculator"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # FENa
    p_fena = sub.add_parser("fena", help="Calculate FENa")
    p_fena.add_argument("--urine-na", type=float, required=True, help="Urine Na (mEq/L)")
    p_fena.add_argument("--plasma-cr", type=float, required=True, help="Plasma Cr (mg/dL)")
    p_fena.add_argument("--plasma-na", type=float, required=True, help="Plasma Na (mEq/L)")
    p_fena.add_argument("--urine-cr", type=float, required=True, help="Urine Cr (mg/dL)")

    # FEUrea
    p_feu = sub.add_parser("feurea", help="Calculate FEUrea")
    p_feu.add_argument("--urine-urea", type=float, required=True, help="Urine urea (mg/dL)")
    p_feu.add_argument("--plasma-cr", type=float, required=True, help="Plasma Cr (mg/dL)")
    p_feu.add_argument("--plasma-bun", type=float, required=True, help="Plasma BUN (mg/dL)")
    p_feu.add_argument("--urine-cr", type=float, required=True, help="Urine Cr (mg/dL)")

    # BUN/Cr ratio
    p_bun = sub.add_parser("bun-cr", help="BUN/Creatinine ratio")
    p_bun.add_argument("--bun", type=float, required=True, help="BUN (mg/dL)")
    p_bun.add_argument("--cr", type=float, required=True, help="Creatinine (mg/dL)")

    # Urine osmolality
    p_osm = sub.add_parser("osmolality", help="Urine osmolality interpretation")
    p_osm.add_argument("--urine-osm", type=float, required=True, help="Urine Osm (mOsm/kg)")
    p_osm.add_argument("--serum-osm", type=float, default=285.0, help="Serum Osm (mOsm/kg)")

    # Specific gravity
    p_sg = sub.add_parser("sg", help="Specific gravity interpretation")
    p_sg.add_argument("--sg", type=float, required=True, help="Specific gravity")

    # Full assessment
    p_full = sub.add_parser("full", help="Full AKI assessment")
    p_full.add_argument("--urine-na", type=float, required=True, help="Urine Na (mEq/L)")
    p_full.add_argument("--plasma-cr", type=float, required=True, help="Plasma Cr (mg/dL)")
    p_full.add_argument("--plasma-na", type=float, required=True, help="Plasma Na (mEq/L)")
    p_full.add_argument("--urine-cr", type=float, required=True, help="Urine Cr (mg/dL)")
    p_full.add_argument("--bun", type=float, required=True, help="BUN (mg/dL)")
    p_full.add_argument("--urine-urea", type=float, default=None, help="Urine urea (mg/dL)")
    p_full.add_argument("--urine-osm", type=float, default=None, help="Urine Osm (mOsm/kg)")
    p_full.add_argument("--sg", type=float, default=None, help="Specific gravity")

    # Audit (supervisor task evaluation)
    p_audit = sub.add_parser("audit", help="Run supervisor audit on a task payload")
    p_audit.add_argument("--task-id", required=True, help="Task identifier")
    p_audit.add_argument("--target-id", default="SPECIMEN-001", help="Target identifier")
    p_audit.add_argument("--primary-metric", type=float, default=10.0, help="Primary measurement")
    p_audit.add_argument("--secondary-metric", type=float, default=4.0, help="Secondary metric")
    p_audit.add_argument("--status-descriptor", default="NOMINAL", help="Status descriptor")
    p_audit.add_argument("--critical", action="store_true", help="Flag as critical")

    # Chat (supervisory LLM query)
    p_chat = sub.add_parser("chat", help="Query the supervisory LLM")
    p_chat.add_argument("query", nargs="+", help="Query text for the LLM")

    # Verify audit integrity
    p_verify = sub.add_parser("verify-audit", help="Verify HMAC-SHA256 audit trail integrity")

    # Serve (FastAPI REST API)
    p_serve = sub.add_parser("serve", help="Start FastAPI REST API server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Bind host")
    p_serve.add_argument("--port", type=int, default=8000, help="Bind port")

    args = parser.parse_args(argv)

    if args.command == "fena":
        result = calc_fena(args.urine_na, args.plasma_cr, args.plasma_na, args.urine_cr)
    elif args.command == "feurea":
        result = calc_feurea(args.urine_urea, args.plasma_cr, args.plasma_bun, args.urine_cr)
    elif args.command == "bun-cr":
        result = calc_bun_cr_ratio(args.bun, args.cr)
    elif args.command == "osmolality":
        result = interpret_urine_osmolality(args.urine_osm, args.serum_osm)
    elif args.command == "sg":
        result = interpret_specific_gravity(args.sg)
    elif args.command == "full":
        result = full_aki_assessment(args.urine_na, args.plasma_cr, args.plasma_na,
                                      args.urine_cr, args.bun, args.urine_urea,
                                      args.urine_osm, 285.0, args.sg)
    elif args.command == "audit":
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target_id,
            primary_metric=args.primary_metric,
            secondary_metric=args.secondary_metric,
            status_descriptor=args.status_descriptor,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        result = dossier.to_dict()
    elif args.command == "chat":
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query)
        try:
            response = supervisor.query_supervisory_chat(query)
        except SecurityException as e:
            print(json.dumps({"error": str(e)}))
            return 1
        result = {"response": response}
    elif args.command == "verify-audit":
        verified = AuditLogger.verify_integrity()
        result = {
            "audit_integrity_verified": verified,
            "total_blocks": len(AuditLogger.get_trail()),
            "algorithm": "HMAC-SHA256",
        }
    elif args.command == "serve":
        import uvicorn
        from agents.api import app
        uvicorn.run(app, host=args.host, port=args.port)
        return 0
    else:
        parser.print_help()
        return 1

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
