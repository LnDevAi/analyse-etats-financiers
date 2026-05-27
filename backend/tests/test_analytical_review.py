"""Tests unitaires — Revue analytique SYSCOHADA N vs N-1"""
import pytest
import pandas as pd
import numpy as np
from app.services.analytical_review import (
    compute_account_balances,
    run_analytical_review,
    SYSCOHADA_CLASSES,
)


def make_df(accounts: dict, fiscal_year: int = 2024) -> pd.DataFrame:
    """
    accounts: {compte_num: (total_debit, total_credit, nb_ecritures)}
    """
    rows = []
    dates = pd.date_range(f"{fiscal_year}-01-01", periods=max(v[2] for v in accounts.values()), freq="ME")
    for compte, (debit, credit, n) in accounts.items():
        for i in range(n):
            rows.append({
                "CompteNum": compte,
                "CompteLib": f"Compte {compte}",
                "EcritureDate": dates[i % len(dates)],
                "EcritureLib": f"Écriture {i}",
                "Debit": debit / n,
                "Credit": credit / n,
            })
    return pd.DataFrame(rows)


ACCOUNTS_N = {
    "411000": (5_000_000, 0, 12),
    "701000": (0, 5_000_000, 12),
    "512000": (3_000_000, 2_500_000, 10),
    "601000": (1_200_000, 0, 8),
}

ACCOUNTS_N1 = {
    "411000": (4_000_000, 0, 10),
    "701000": (0, 4_000_000, 10),
    "512000": (2_000_000, 1_800_000, 8),
    "601000": (800_000, 0, 6),
}

ACCOUNTS_N_LARGE_DEVIATION = {
    "411000": (10_000_000, 0, 12),  # +150% vs N-1
    "701000": (0, 10_000_000, 12),
    "601000": (3_000_000, 0, 10),
}


class TestComputeAccountBalances:
    def test_basic_balances(self):
        df = make_df(ACCOUNTS_N)
        result = compute_account_balances(df)
        assert len(result) == len(ACCOUNTS_N)
        assert "solde_net" in result.columns
        assert "classe_lib" in result.columns

    def test_solde_correct(self):
        df = make_df({"411000": (500_000, 0, 5)})
        result = compute_account_balances(df)
        row = result[result["CompteNum"] == "411000"].iloc[0]
        assert abs(row["solde_net"] - 500_000) < 1.0

    def test_classe_lib_mapped(self):
        df = make_df({"701000": (0, 1_000_000, 5)})
        result = compute_account_balances(df)
        row = result.iloc[0]
        assert row["classe_lib"] == SYSCOHADA_CLASSES["7"]

    def test_missing_compte_num_returns_empty(self):
        df = pd.DataFrame({"Debit": [100.0], "Credit": [0.0]})
        result = compute_account_balances(df)
        assert result.empty

    def test_compte_lib_attached(self):
        df = make_df({"512000": (100_000, 50_000, 3)})
        result = compute_account_balances(df)
        assert "compte_lib" in result.columns

    def test_nb_ecritures_counted(self):
        df = make_df({"601000": (1_200_000, 0, 8)})
        result = compute_account_balances(df)
        row = result[result["CompteNum"] == "601000"].iloc[0]
        assert row["nb_ecritures"] == 8


class TestRunAnalyticalReview:
    def test_single_year_analysis(self):
        df = make_df(ACCOUNTS_N)
        result = run_analytical_review(df)
        assert "fiscal_year_n" in result
        assert result["fiscal_year_n"]["total_accounts"] == len(ACCOUNTS_N)
        assert "comparison_n_vs_n1" not in result

    def test_by_class_structure(self):
        df = make_df(ACCOUNTS_N)
        result = run_analytical_review(df)
        by_class = result["fiscal_year_n"]["by_class"]
        assert isinstance(by_class, dict)
        # Classe 4 (tiers) et 7 (produits) doivent être présents
        class_libs = list(by_class.keys())
        assert any("tiers" in k.lower() or "produits" in k.lower() for k in class_libs)

    def test_high_volume_accounts_present(self):
        df = make_df(ACCOUNTS_N)
        result = run_analytical_review(df)
        assert "high_volume_accounts" in result
        assert len(result["high_volume_accounts"]) <= 10

    def test_risk_level_vert_when_no_deviations(self):
        df_n = make_df(ACCOUNTS_N)
        df_n1 = make_df(ACCOUNTS_N)  # Identique → pas de déviation
        result = run_analytical_review(df_n, df_n1)
        assert result["risk_level"] == "VERT"

    def test_nv_n1_comparison_present(self):
        df_n = make_df(ACCOUNTS_N)
        df_n1 = make_df(ACCOUNTS_N1)
        result = run_analytical_review(df_n, df_n1)
        assert "comparison_n_vs_n1" in result
        comp = result["comparison_n_vs_n1"]
        assert "deviations_count" in comp
        assert "deviations" in comp
        assert comp["deviations_count"] > 0

    def test_large_deviation_gives_rouge(self):
        df_n = make_df(ACCOUNTS_N_LARGE_DEVIATION)
        df_n1 = make_df({"411000": (4_000_000, 0, 10), "701000": (0, 4_000_000, 10), "601000": (600_000, 0, 6)})
        result = run_analytical_review(df_n, df_n1)
        assert result["risk_level"] == "ROUGE"
        deviations = result["comparison_n_vs_n1"]["deviations"]
        rouge_devs = [d for d in deviations if d["severity"] == "ROUGE"]
        assert len(rouge_devs) > 0

    def test_new_account_in_n(self):
        """Un compte présent en N mais absent en N-1 est une déviation."""
        df_n = make_df({"411000": (5_000_000, 0, 10), "699000": (500_000, 0, 5)})
        df_n1 = make_df({"411000": (4_000_000, 0, 8)})
        result = run_analytical_review(df_n, df_n1)
        accounts_in_devs = [d["account"] for d in result["comparison_n_vs_n1"]["deviations"]]
        assert "699000" in accounts_in_devs

    def test_missing_compte_num_returns_error(self):
        df = pd.DataFrame({"Debit": [100.0], "Credit": [0.0]})
        result = run_analytical_review(df)
        assert "error" in result

    def test_threshold_respected(self):
        """Avec un seuil très élevé, peu de déviations remontent."""
        df_n = make_df(ACCOUNTS_N)
        df_n1 = make_df(ACCOUNTS_N1)
        result_strict = run_analytical_review(df_n, df_n1, threshold_pct=80.0)
        result_loose = run_analytical_review(df_n, df_n1, threshold_pct=5.0)
        assert result_strict["comparison_n_vs_n1"]["deviations_count"] <= result_loose["comparison_n_vs_n1"]["deviations_count"]

    def test_empty_previous_df(self):
        df_n = make_df(ACCOUNTS_N)
        df_n1_empty = pd.DataFrame()
        result = run_analytical_review(df_n, df_n1_empty)
        # df_previous vide → pas de comparaison
        assert "comparison_n_vs_n1" not in result
