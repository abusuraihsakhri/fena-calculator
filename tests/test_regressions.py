import math
import os

os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-not-for-production")

import pytest
from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from fena import (
    calc_fena, calc_feurea, calc_bun_cr_ratio,
    interpret_urine_osmolality, interpret_specific_gravity,
    full_aki_assessment,
)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_fractional_excretion_rejects_nonfinite(bad):
    with pytest.raises(ValueError):
        calc_fena(bad, 2.0, 140.0, 200.0)
    with pytest.raises(ValueError):
        calc_feurea(100, 2.0, bad, 200.0)
    with pytest.raises(ValueError):
        calc_bun_cr_ratio(50, bad)
    with pytest.raises(ValueError):
        interpret_urine_osmolality(bad)
    with pytest.raises(ValueError):
        interpret_specific_gravity(bad)


def test_negative_urine_osmolality_rejected():
    with pytest.raises(ValueError):
        interpret_urine_osmolality(-1)


def test_rounding_does_not_alter_full_assessment_classification():
    # FENa is 0.999%: the reported 1.00% must retain its prerenal category.
    result = full_aki_assessment(
        urine_na=99.9, plasma_cr=1, plasma_na=100, urine_cr=100,
        bun=25,
    )
    assert result["fena"]["fena_percent"] == 1.0
    assert result["fena"]["interpretation"] == "Prerenal azotemia"
    assert "Prerenal" in result["overall_assessment"]


def test_hmac_checks_each_signed_field_and_hash():
    chain = AuditTrail(secret_key="isolated-unit-test-secret")
    first = chain.log("worker", "test", "START", {"value": 3})
    second = chain.log("worker", "test", "END", {"value": 4})
    assert chain.verify_integrity()
    second["event_type"] = "REPLACED"
    assert not chain.verify_integrity()
    second["event_type"] = "END"
    assert chain.verify_integrity()
    first["current_hash"] = "0" * 64
    assert not chain.verify_integrity()


def test_nested_metadata_phi_guard():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TEST-ONLY-1", target_identifier="KEY-1",
        primary_metric=1.0,
        attributes={"details": {"contact": "patient@example.com"}},
    )
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)
