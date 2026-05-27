"""Tests unitaires — Loi de Benford"""
import pandas as pd
import numpy as np
import pytest
from app.services.benford import run_benford_analysis, get_first_digit, BENFORD_DISTRIBUTION


def make_benford_df(n=500) -> pd.DataFrame:
    """Génère un FEC synthétique suivant la loi de Benford."""
    rng = np.random.default_rng(42)
    digits = rng.choice(list(BENFORD_DISTRIBUTION.keys()), size=n, p=list(BENFORD_DISTRIBUTION.values()))
    amounts = [d * 10 ** rng.integers(1, 6) + rng.random() * 1000 for d in digits]
    return pd.DataFrame({"Debit": amounts, "Credit": [0.0] * n})


def make_fraudulent_df(n=500) -> pd.DataFrame:
    """FEC avec distribution anormale (trop de 1 et 9)."""
    rng = np.random.default_rng(0)
    digits = rng.choice([1, 9], size=n, p=[0.7, 0.3])
    amounts = [d * rng.integers(100, 10000) for d in digits]
    return pd.DataFrame({"Debit": amounts, "Credit": [0.0] * n})


class TestGetFirstDigit:
    def test_single_digit(self):
        assert get_first_digit(5.0) == 5

    def test_large_number(self):
        assert get_first_digit(12345.0) == 1

    def test_small_decimal(self):
        assert get_first_digit(0.00345) == 3

    def test_negative_not_processed(self):
        assert get_first_digit(-100.0) is None

    def test_zero_returns_none(self):
        assert get_first_digit(0.0) is None


class TestBenfordAnalysis:
    def test_conforming_data(self):
        df = make_benford_df(1000)
        result = run_benford_analysis(df, "Debit")
        assert result["sufficient_data"] is True
        assert result["conformity_score"] >= 60
        assert result["risk_level"] in ("VERT", "ORANGE")

    def test_fraudulent_data(self):
        df = make_fraudulent_df(500)
        result = run_benford_analysis(df, "Debit")
        assert result["sufficient_data"] is True
        assert result["p_value"] < 0.05
        assert result["risk_level"] == "ROUGE"

    def test_insufficient_data(self):
        df = pd.DataFrame({"Debit": [100.0, 200.0, 300.0]})
        result = run_benford_analysis(df, "Debit")
        assert result["sufficient_data"] is False

    def test_distribution_keys(self):
        df = make_benford_df(500)
        result = run_benford_analysis(df, "Debit")
        assert set(result["distribution"].keys()) == set(range(1, 10))

    def test_missing_column(self):
        df = pd.DataFrame({"MontantX": [100.0, 200.0]})
        with pytest.raises(KeyError):
            run_benford_analysis(df, "Debit")
