"""Tests unitaires — Calcul du score de risque"""
import pytest
from app.services.risk_scorer import compute_risk_score, RISK_WEIGHTS


class TestComputeRiskScore:
    def test_all_vert_gives_high_score(self):
        result = compute_risk_score(
            intrinsic_check={"valid": True, "difference": 0},
            benford_result={"risk_level": "VERT"},
            isolation_forest_result={"risk_level": "VERT"},
            analytical_review={"risk_level": "VERT"},
            cycle_ventes_result={"risk_level": "VERT"},
            cycle_tresorerie_result={"risk_level": "VERT"},
        )
        assert result["global_score"] >= 75
        assert result["risk_level"] == "VERT"

    def test_all_rouge_gives_low_score(self):
        result = compute_risk_score(
            intrinsic_check={"valid": False, "difference": 999999},
            benford_result={"risk_level": "ROUGE"},
            isolation_forest_result={"risk_level": "ROUGE"},
            analytical_review={"risk_level": "ROUGE"},
            cycle_ventes_result={"risk_level": "ROUGE"},
            cycle_tresorerie_result={"risk_level": "ROUGE"},
        )
        assert result["global_score"] < 45
        assert result["risk_level"] == "ROUGE"

    def test_mixed_gives_orange(self):
        result = compute_risk_score(
            intrinsic_check={"valid": True, "difference": 0},
            benford_result={"risk_level": "ORANGE"},
            isolation_forest_result={"risk_level": "ORANGE"},
        )
        assert result["risk_level"] in ("ORANGE", "VERT")

    def test_no_modules_defaults_to_vert(self):
        result = compute_risk_score()
        assert result["risk_level"] == "VERT"
        assert result["global_score"] == 100.0

    def test_weights_sum_to_one(self):
        total = sum(RISK_WEIGHTS.values())
        assert abs(total - 1.0) < 0.0001

    def test_interpretation_present(self):
        result = compute_risk_score()
        assert "interpretation" in result
        assert len(result["interpretation"]) > 10

    def test_score_in_range(self):
        result = compute_risk_score(
            benford_result={"risk_level": "ROUGE"},
            cycle_tresorerie_result={"risk_level": "ORANGE"},
        )
        assert 0 <= result["global_score"] <= 100
