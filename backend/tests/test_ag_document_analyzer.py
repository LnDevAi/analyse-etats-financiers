"""Tests for the AG comparative analysis service."""
import io
import json
import pytest
import pandas as pd
import numpy as np

from app.services.ag_document_analyzer import (
    run_budget_execution_analysis,
    run_masse_salariale_check,
    run_marches_check,
    run_activites_check,
    run_ag_comparative_analysis,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def make_fec(rows: list[dict]) -> pd.DataFrame:
    defaults = {
        "JournalCode": "OD",
        "EcritureDate": "20240101",
        "CompteNum": "601000",
        "CompteLib": "Achats",
        "Debit": 0.0,
        "Credit": 0.0,
        "EcritureLib": "libellé",
    }
    data = [{**defaults, **r} for r in rows]
    return pd.DataFrame(data)


def csv_budget(rows: list[str]) -> bytes:
    """Build a minimal CSV budget document."""
    header = "classe;budget_prevu;realise_doc\n"
    return (header + "\n".join(rows)).encode("utf-8")


def csv_social(masse: float) -> bytes:
    return f"Masse salariale;{masse:.0f}\n".encode("utf-8")


def csv_marches(rows: list[str]) -> bytes:
    header = "libelle;montant_marche\n"
    return (header + "\n".join(rows)).encode("utf-8")


def txt_activites(text: str) -> bytes:
    return text.encode("utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# run_budget_execution_analysis
# ──────────────────────────────────────────────────────────────────────────────

class TestRunBudgetExecutionAnalysis:
    def _df_with_class6(self, amount=500_000):
        return make_fec([{"CompteNum": "601000", "Debit": amount, "Credit": 0}])

    def test_returns_dict_with_required_keys(self):
        df = self._df_with_class6()
        budget = csv_budget(["6;1000000;500000"])
        result = run_budget_execution_analysis(df, budget, "budget.csv")
        assert isinstance(result, dict)
        assert "coherence_score" in result
        assert "risk_level" in result

    def test_coherence_score_in_range(self):
        df = self._df_with_class6()
        budget = csv_budget(["6;1000000;500000"])
        result = run_budget_execution_analysis(df, budget, "budget.csv")
        score = result["coherence_score"]
        assert 0.0 <= score <= 1.0

    def test_perfect_match_gives_high_score(self):
        df = make_fec([{"CompteNum": "601000", "Debit": 500_000, "Credit": 0}])
        # Budget says same as FEC
        budget = csv_budget(["6;500000;500000"])
        result = run_budget_execution_analysis(df, budget, "budget.csv")
        assert result["coherence_score"] >= 0.7

    def test_large_gap_gives_rouge(self):
        df = make_fec([{"CompteNum": "601000", "Debit": 100_000, "Credit": 0}])
        # Budget says 10× more
        budget = csv_budget(["6;1000000;1000000"])
        result = run_budget_execution_analysis(df, budget, "budget.csv")
        assert result["risk_level"] in ("ORANGE", "ROUGE")

    def test_no_budget_content_returns_defaults(self):
        df = self._df_with_class6()
        result = run_budget_execution_analysis(df, None, "budget.csv")
        assert result["coherence_score"] == 1.0
        assert result["risk_level"] == "VERT"

    def test_comparaison_par_classe_present(self):
        df = self._df_with_class6()
        budget = csv_budget(["6;1000000;500000"])
        result = run_budget_execution_analysis(df, budget, "budget.csv")
        assert "comparaison_par_classe" in result


# ──────────────────────────────────────────────────────────────────────────────
# run_masse_salariale_check
# ──────────────────────────────────────────────────────────────────────────────

class TestRunMasseSalarialeCheck:
    def _df_with_66x(self, amount=2_000_000):
        return make_fec([{"CompteNum": "661000", "Debit": amount, "Credit": 0}])

    def test_returns_required_keys(self):
        df = self._df_with_66x()
        result = run_masse_salariale_check(df, csv_social(2_000_000), "bilan.csv")
        assert "masse_salariale_fec" in result
        assert "masse_salariale_document" in result
        assert "coherence_score" in result
        assert "risk_level" in result

    def test_equal_amounts_vert(self):
        df = self._df_with_66x(2_000_000)
        result = run_masse_salariale_check(df, csv_social(2_000_000), "bilan.csv")
        assert result["risk_level"] == "VERT"

    def test_large_gap_rouge(self):
        df = self._df_with_66x(500_000)
        result = run_masse_salariale_check(df, csv_social(5_000_000), "bilan.csv")
        assert result["risk_level"] in ("ORANGE", "ROUGE")

    def test_no_social_doc_returns_defaults(self):
        df = self._df_with_66x()
        result = run_masse_salariale_check(df, None, "bilan.csv")
        assert result["coherence_score"] == 1.0
        assert result["risk_level"] == "VERT"

    def test_fec_amount_matches_66x_accounts(self):
        df = make_fec([
            {"CompteNum": "661000", "Debit": 1_000_000, "Credit": 0},
            {"CompteNum": "664000", "Debit": 500_000, "Credit": 0},
        ])
        result = run_masse_salariale_check(df, csv_social(1_500_000), "bilan.csv")
        assert abs(result["masse_salariale_fec"] - 1_500_000) < 1


# ──────────────────────────────────────────────────────────────────────────────
# run_marches_check
# ──────────────────────────────────────────────────────────────────────────────

class TestRunMarchesCheck:
    def _df_with_40x(self, amount=800_000):
        return make_fec([{"CompteNum": "401000", "Credit": amount, "Debit": 0}])

    def test_returns_required_keys(self):
        df = self._df_with_40x()
        result = run_marches_check(df, csv_marches(["Travaux;800000"]), "marches.csv")
        assert "coherence_score" in result
        assert "risk_level" in result

    def test_no_marches_doc_returns_defaults(self):
        df = self._df_with_40x()
        result = run_marches_check(df, None, "marches.csv")
        assert result["coherence_score"] == 1.0
        assert result["risk_level"] == "VERT"

    def test_matching_amounts_high_score(self):
        df = self._df_with_40x(800_000)
        result = run_marches_check(df, csv_marches(["Travaux;800000"]), "marches.csv")
        assert result["coherence_score"] >= 0.5

    def test_marches_compares_list_present(self):
        df = self._df_with_40x()
        result = run_marches_check(df, csv_marches(["Travaux;800000", "Services;200000"]), "marches.csv")
        assert "marches_compares" in result


# ──────────────────────────────────────────────────────────────────────────────
# run_activites_check
# ──────────────────────────────────────────────────────────────────────────────

class TestRunActivitesCheck:
    def _df_basic(self):
        return make_fec([{"CompteNum": "701000", "Credit": 1_000_000, "Debit": 0}])

    def test_returns_required_keys(self):
        df = self._df_basic()
        result = run_activites_check(df, txt_activites("Montant 1 000 000 FCFA"), "rapport.txt")
        assert "coherence_score" in result
        assert "risk_level" in result

    def test_no_activites_doc_returns_defaults(self):
        df = self._df_basic()
        result = run_activites_check(df, None, "rapport.txt")
        assert result["coherence_score"] == 1.0

    def test_score_in_range(self):
        df = self._df_basic()
        result = run_activites_check(df, txt_activites("Budget 500 000 FCFA alloué"), "rapport.txt")
        assert 0.0 <= result["coherence_score"] <= 1.0


# ──────────────────────────────────────────────────────────────────────────────
# run_ag_comparative_analysis (orchestrator)
# ──────────────────────────────────────────────────────────────────────────────

class TestRunAgComparativeAnalysis:
    def _base_df(self):
        return make_fec([
            {"CompteNum": "601000", "Debit": 1_000_000, "Credit": 0},
            {"CompteNum": "661000", "Debit": 500_000, "Credit": 0},
            {"CompteNum": "401000", "Credit": 300_000, "Debit": 0},
            {"CompteNum": "701000", "Credit": 2_000_000, "Debit": 0},
        ])

    def test_returns_all_section_keys(self):
        df = self._base_df()
        result = run_ag_comparative_analysis(df_fec=df)
        assert "global" in result
        assert "budget_execution" in result
        assert "masse_salariale" in result
        assert "marches" in result
        assert "activites" in result

    def test_global_has_coherence_score(self):
        df = self._base_df()
        result = run_ag_comparative_analysis(df_fec=df)
        assert "coherence_score" in result["global"]
        assert 0.0 <= result["global"]["coherence_score"] <= 1.0

    def test_global_risk_level_valid_value(self):
        df = self._base_df()
        result = run_ag_comparative_analysis(df_fec=df)
        assert result["global"]["risk_level"] in ("VERT", "ORANGE", "ROUGE")

    def test_with_all_docs(self):
        df = self._base_df()
        result = run_ag_comparative_analysis(
            df_fec=df,
            budget_content=csv_budget(["6;1000000;900000"]),
            budget_filename="budget.csv",
            social_content=csv_social(500_000),
            social_filename="bilan.csv",
            marches_content=csv_marches(["Route;300000"]),
            marches_filename="marches.csv",
            activites_content=txt_activites("Montant 2 000 000 FCFA"),
            activites_filename="rapport.txt",
        )
        assert result["global"]["coherence_score"] is not None

    def test_no_optional_docs_succeeds(self):
        df = self._base_df()
        result = run_ag_comparative_analysis(df_fec=df)
        # All four modules should still return with default VERT
        for module in ("budget_execution", "masse_salariale", "marches", "activites"):
            assert result[module]["risk_level"] == "VERT"

    def test_global_interpretation_is_string(self):
        df = self._base_df()
        result = run_ag_comparative_analysis(df_fec=df)
        interp = result["global"].get("interpretation")
        assert isinstance(interp, str) and len(interp) > 0
