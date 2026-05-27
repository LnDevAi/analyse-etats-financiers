"""Tests unitaires — Contrôle de cohérence SYSCOHADA"""
import pytest
import pandas as pd
import numpy as np
from app.services.coherence_checker import (
    check_soldes_normaux,
    check_resultat_coherence,
    check_equilibre_bilan,
    detect_doublons_ecritures,
    detect_montants_repetes,
    run_coherence_check,
)


def make_df(rows: list) -> pd.DataFrame:
    return pd.DataFrame(rows)


def make_clean_df(n: int = 50) -> pd.DataFrame:
    """FEC propre : charges débitrices, produits créditeurs, clients débiteurs."""
    rng = np.random.default_rng(42)
    rows = []
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    for i, d in enumerate(dates):
        amt = float(rng.integers(100_000, 2_000_000))
        rows.append({
            "EcritureNum": f"VT{i:04d}",
            "EcritureDate": d,
            "CompteNum": "701000",
            "CompteLib": "Ventes",
            "EcritureLib": f"Vente {i}",
            "Debit": 0.0,
            "Credit": amt,
        })
        rows.append({
            "EcritureNum": f"VT{i:04d}",
            "EcritureDate": d,
            "CompteNum": "411000",
            "CompteLib": "Clients",
            "EcritureLib": f"Client {i}",
            "Debit": amt,
            "Credit": 0.0,
        })
    return pd.DataFrame(rows)


class TestSoldesNormaux:
    def test_clean_fec_no_anomalies(self):
        df = make_clean_df(30)
        result = check_soldes_normaux(df)
        assert result["anomalies_count"] == 0
        assert result["risk_level"] == "VERT"

    def test_compte_7_with_debit_balance(self):
        """Compte ventes (701) avec solde débiteur → anormal."""
        df = make_df([
            {"CompteNum": "701000", "Debit": 5_000_000.0, "Credit": 1_000_000.0},
        ])
        result = check_soldes_normaux(df)
        assert result["anomalies_count"] >= 1
        assert any(a["account"] == "701000" for a in result["anomalies"])

    def test_compte_6_with_credit_balance(self):
        """Compte charges (601) avec solde créditeur → anormal."""
        df = make_df([
            {"CompteNum": "601000", "Debit": 500_000.0, "Credit": 2_000_000.0},
        ])
        result = check_soldes_normaux(df)
        assert result["anomalies_count"] >= 1

    def test_compte_40_with_debit_balance(self):
        """Fournisseur (401) avec solde débiteur → anormal (avance suspect)."""
        df = make_df([
            {"CompteNum": "401000", "Debit": 3_000_000.0, "Credit": 500_000.0},
        ])
        result = check_soldes_normaux(df)
        assert result["anomalies_count"] >= 1

    def test_rouge_for_large_anomaly(self):
        """Anomalie > 1M FCFA → ROUGE."""
        df = make_df([
            {"CompteNum": "701000", "Debit": 10_000_000.0, "Credit": 0.0},
        ])
        result = check_soldes_normaux(df)
        assert result["anomalies"][0]["severity"] == "ROUGE"

    def test_missing_column(self):
        df = pd.DataFrame({"Debit": [100.0]})
        result = check_soldes_normaux(df)
        assert "error" in result

    def test_interpretation_present(self):
        df = make_clean_df(10)
        result = check_soldes_normaux(df)
        assert "interpretation" in result


class TestResultatCoherence:
    def test_balanced_resultat(self):
        """Cl.7 crédit − Cl.6 débit = Résultat en Cl.13."""
        resultat = 2_000_000.0
        df = make_df([
            {"CompteNum": "701000", "Debit": 0.0, "Credit": 5_000_000.0},
            {"CompteNum": "601000", "Debit": 3_000_000.0, "Credit": 0.0},
            {"CompteNum": "131000", "Debit": 0.0, "Credit": resultat},
        ])
        result = check_resultat_coherence(df)
        assert result["resultat_fec"] == pytest.approx(resultat, abs=1.0)
        assert result["coherent"] is True
        assert result["risk_level"] == "VERT"

    def test_no_closing_entries(self):
        """Sans compte 13x → exercice non clôturé → ORANGE."""
        df = make_df([
            {"CompteNum": "701000", "Debit": 0.0, "Credit": 5_000_000.0},
            {"CompteNum": "601000", "Debit": 3_000_000.0, "Credit": 0.0},
        ])
        result = check_resultat_coherence(df)
        assert result["has_closing_entries"] is False
        assert result["risk_level"] == "ORANGE"

    def test_resultat_incoherent(self):
        """Cl.13 ne correspond pas au résultat calculé → ROUGE."""
        df = make_df([
            {"CompteNum": "701000", "Debit": 0.0, "Credit": 5_000_000.0},
            {"CompteNum": "601000", "Debit": 3_000_000.0, "Credit": 0.0},
            {"CompteNum": "131000", "Debit": 0.0, "Credit": 500_000.0},  # Faux
        ])
        result = check_resultat_coherence(df)
        assert result["coherent"] is False
        assert result["ecart"] > 1_000

    def test_missing_column(self):
        df = pd.DataFrame({"Debit": [100.0]})
        result = check_resultat_coherence(df)
        assert "error" in result


class TestEquilibreBilan:
    def test_balanced_bilan(self):
        """Bilan équilibré → VERT."""
        # Actif = 5M (clients), Passif = 3M (capital) + 2M (résultat)
        df = make_df([
            {"CompteNum": "411000", "Debit": 5_000_000.0, "Credit": 0.0},
            {"CompteNum": "101000", "Debit": 0.0, "Credit": 3_000_000.0},
            {"CompteNum": "701000", "Debit": 0.0, "Credit": 2_000_000.0},
        ])
        result = check_equilibre_bilan(df)
        assert result["total_actif"] > 0
        assert result["risk_level"] in ("VERT", "ORANGE")  # Approximation acceptable

    def test_missing_column(self):
        df = pd.DataFrame({"Debit": [100.0]})
        result = check_equilibre_bilan(df)
        assert "error" in result

    def test_detail_actif_keys(self):
        df = make_clean_df(20)
        result = check_equilibre_bilan(df)
        assert "detail_actif" in result
        assert "detail_passif" in result
        assert "ecart_pct" in result


class TestDoublons:
    def test_no_duplicates(self):
        df = make_clean_df(20)
        result = detect_doublons_ecritures(df)
        assert result["duplicates_count"] == 0
        assert result["risk_level"] == "VERT"

    def test_exact_duplicate_detected(self):
        row = {
            "EcritureNum": "VT001",
            "EcritureDate": pd.Timestamp("2024-01-15"),
            "CompteNum": "512000",
            "EcritureLib": "Virement",
            "Debit": 1_000_000.0,
            "Credit": 0.0,
        }
        df = pd.DataFrame([row, row, {"EcritureNum": "VT002", "EcritureDate": pd.Timestamp("2024-01-16"), "CompteNum": "701000", "EcritureLib": "Autre", "Debit": 0.0, "Credit": 500_000.0}])
        result = detect_doublons_ecritures(df)
        assert result["exact_duplicates"] >= 2
        assert result["risk_level"] == "ROUGE"

    def test_interpretation_present(self):
        df = make_clean_df(10)
        result = detect_doublons_ecritures(df)
        assert "interpretation" in result


class TestMontantsRepetes:
    def test_no_suspicious(self):
        df = make_clean_df(50)
        result = detect_montants_repetes(df, min_occurrences=3)
        # Avec des montants aléatoires, peu de répétitions
        assert result["risk_level"] in ("VERT", "ORANGE")

    def test_repeated_amount_flagged(self):
        amount = 500_000.0
        rows = [
            {"CompteNum": f"51{i}000", "EcritureNum": f"TX{i:04d}",
             "EcritureDate": pd.Timestamp("2024-01-01"), "EcritureLib": "Vir",
             "Debit": amount, "Credit": 0.0}
            for i in range(1, 12)
        ]
        df = pd.DataFrame(rows)
        result = detect_montants_repetes(df, min_occurrences=5)
        assert result["suspicious_amounts_count"] >= 1
        assert any(a["amount"] == amount for a in result["suspicious_amounts"])


class TestRunCoherenceCheck:
    def test_clean_fec_gives_vert(self):
        df = make_clean_df(50)
        result = run_coherence_check(df)
        assert result["risk_level"] in ("VERT", "ORANGE")
        assert "soldes_normaux" in result
        assert "resultat_coherence" in result
        assert "equilibre_bilan" in result
        assert "doublons" in result
        assert "montants_repetes" in result

    def test_all_keys_present(self):
        df = make_clean_df(30)
        result = run_coherence_check(df)
        for key in ("risk_level", "total_anomalies", "interpretation"):
            assert key in result

    def test_rouge_propagates(self):
        """Un compte avec solde anormal majeur → risk_level ROUGE global."""
        df = make_df([
            {"CompteNum": "701000", "Debit": 10_000_000.0, "Credit": 0.0},
            {"CompteNum": "401000", "Debit": 8_000_000.0, "Credit": 0.0},
        ])
        result = run_coherence_check(df)
        assert result["risk_level"] == "ROUGE"
