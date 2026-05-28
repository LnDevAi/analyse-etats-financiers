"""Tests unitaires — Audit des cycles critiques SYSCOHADA"""
import pytest
import pandas as pd
import numpy as np
from app.services.cycle_audit import run_cycle_ventes, run_cycle_tresorerie


def make_ventes_df(fiscal_year: int = 2024, n_normal: int = 50, n_cutoff: int = 0):
    """Génère un FEC avec des ventes, dont certaines hors période."""
    dates_in = pd.date_range(f"{fiscal_year}-01-15", f"{fiscal_year}-11-30", periods=n_normal)
    rows = []
    for d in dates_in:
        rows.append({
            "CompteNum": "701000",
            "CompteLib": "Ventes marchandises",
            "EcritureDate": d,
            "EcritureLib": "Vente client",
            "Debit": 0.0,
            "Credit": 500_000.0,
        })
        rows.append({
            "CompteNum": "411000",
            "CompteLib": "Clients",
            "EcritureDate": d,
            "EcritureLib": "Vente client",
            "Debit": 500_000.0,
            "Credit": 0.0,
        })

    # Ventes hors période (cutoff)
    cutoff_dates = pd.date_range(f"{fiscal_year - 2}-01-01", periods=n_cutoff, freq="MS")
    for d in cutoff_dates:
        rows.append({
            "CompteNum": "701000",
            "CompteLib": "Ventes marchandises",
            "EcritureDate": d,
            "EcritureLib": "Vente rattrapée",
            "Debit": 0.0,
            "Credit": 250_000.0,
        })

    return pd.DataFrame(rows)


def make_tresorerie_df(
    n_normal: int = 20,
    include_weekend: bool = False,
    include_round: bool = False,
    include_no_label: bool = False,
):
    rng = np.random.default_rng(7)
    rows = []

    dates = pd.date_range("2024-01-02", periods=n_normal, freq="B")
    for d in dates:
        rows.append({
            "CompteNum": "512000",
            "CompteLib": "Banque BIS",
            "EcritureDate": d,
            "EcritureLib": "Virement fournisseur",
            "Debit": float(rng.integers(50_000, 300_000)),
            "Credit": 0.0,
        })

    if include_weekend:
        rows.append({
            "CompteNum": "512000",
            "CompteLib": "Banque BIS",
            "EcritureDate": pd.Timestamp("2024-02-10"),  # Samedi
            "EcritureLib": "Retrait week-end",
            "Debit": 500_000.0,
            "Credit": 0.0,
        })

    if include_round:
        rows.append({
            "CompteNum": "512000",
            "CompteLib": "Banque BIS",
            "EcritureDate": pd.Timestamp("2024-03-15"),
            "EcritureLib": "Virement rond",
            "Debit": 5_000_000.0,
            "Credit": 0.0,
        })

    if include_no_label:
        rows.append({
            "CompteNum": "512000",
            "CompteLib": "Banque BIS",
            "EcritureDate": pd.Timestamp("2024-04-01"),
            "EcritureLib": "",
            "Debit": 200_000.0,
            "Credit": 0.0,
        })

    return pd.DataFrame(rows)


class TestCycleVentes:
    def test_no_cutoff_anomalies(self):
        df = make_ventes_df(fiscal_year=2024, n_normal=30, n_cutoff=0)
        result = run_cycle_ventes(df, fiscal_year=2024)
        assert result["cutoff_anomalies_count"] == 0
        assert result["risk_level"] == "VERT"

    def test_few_cutoff_gives_orange(self):
        df = make_ventes_df(fiscal_year=2024, n_normal=20, n_cutoff=5)
        result = run_cycle_ventes(df, fiscal_year=2024)
        assert result["cutoff_anomalies_count"] == 5
        assert result["risk_level"] == "ORANGE"

    def test_many_cutoff_gives_rouge(self):
        df = make_ventes_df(fiscal_year=2024, n_normal=20, n_cutoff=15)
        result = run_cycle_ventes(df, fiscal_year=2024)
        assert result["cutoff_anomalies_count"] >= 10
        assert result["risk_level"] == "ROUGE"

    def test_fiscal_year_inferred_when_none(self):
        df = make_ventes_df(fiscal_year=2024, n_normal=20)
        result = run_cycle_ventes(df, fiscal_year=None)
        assert result["fiscal_year_analyzed"] == 2024

    def test_ventes_entries_counted(self):
        df = make_ventes_df(fiscal_year=2024, n_normal=15, n_cutoff=0)
        result = run_cycle_ventes(df, fiscal_year=2024)
        assert result["ventes_entries"] == 15
        assert result["clients_entries"] == 15

    def test_monthly_breakdown_present(self):
        df = make_ventes_df(fiscal_year=2024, n_normal=12, n_cutoff=0)
        result = run_cycle_ventes(df, fiscal_year=2024)
        assert isinstance(result["monthly_ventes"], dict)
        assert len(result["monthly_ventes"]) >= 1

    def test_missing_column_returns_error(self):
        df = pd.DataFrame({"Debit": [1.0, 2.0], "Credit": [0.0, 0.0]})
        result = run_cycle_ventes(df, fiscal_year=2024)
        assert "error" in result

    def test_interpretation_present(self):
        df = make_ventes_df(fiscal_year=2024, n_normal=10)
        result = run_cycle_ventes(df, fiscal_year=2024)
        assert "interpretation" in result
        assert len(result["interpretation"]) > 5


class TestCycleTresorerie:
    def test_normal_transactions_vert(self):
        df = make_tresorerie_df(n_normal=20)
        result = run_cycle_tresorerie(df)
        assert result["risk_level"] == "VERT"
        assert result["tresorerie_entries"] == 20

    def test_weekend_high_amount_rouge(self):
        df = make_tresorerie_df(n_normal=10, include_weekend=True)
        result = run_cycle_tresorerie(df)
        rouge_flags = [s for s in result["suspicious_transactions"] if s["type"] == "WEEKEND_HIGH_AMOUNT"]
        assert len(rouge_flags) >= 1
        assert result["risk_level"] == "ROUGE"

    def test_round_amount_detected(self):
        df = make_tresorerie_df(n_normal=10, include_round=True)
        result = run_cycle_tresorerie(df)
        round_flags = [s for s in result["suspicious_transactions"] if s["type"] == "MONTANT_ROND_SUSPECT"]
        assert len(round_flags) >= 1

    def test_no_label_detected(self):
        df = make_tresorerie_df(n_normal=5, include_no_label=True)
        result = run_cycle_tresorerie(df)
        no_label = [s for s in result["suspicious_transactions"] if s["type"] == "SANS_LIBELLE"]
        assert len(no_label) >= 1

    def test_breakdown_keys_present(self):
        df = make_tresorerie_df(n_normal=10, include_weekend=True, include_round=True, include_no_label=True)
        result = run_cycle_tresorerie(df)
        assert "breakdown" in result
        assert "sans_libelle" in result["breakdown"]
        assert "weekend" in result["breakdown"]
        assert "montant_rond" in result["breakdown"]

    def test_missing_column_returns_error(self):
        df = pd.DataFrame({"Debit": [1.0], "Credit": [0.0]})
        result = run_cycle_tresorerie(df)
        assert "error" in result

    def test_no_tresorerie_accounts_returns_error(self):
        df = pd.DataFrame({
            "CompteNum": ["401000", "411000"],
            "EcritureDate": [pd.Timestamp("2024-01-10")] * 2,
            "EcritureLib": ["Fournisseur", "Client"],
            "Debit": [100_000.0, 0.0],
            "Credit": [0.0, 100_000.0],
        })
        result = run_cycle_tresorerie(df)
        assert "error" in result

    def test_total_flux_positive(self):
        df = make_tresorerie_df(n_normal=15)
        result = run_cycle_tresorerie(df)
        assert result["total_flux"] > 0
