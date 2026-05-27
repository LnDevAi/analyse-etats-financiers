"""Fixtures partagées pour les tests unitaires."""
import pytest
import pandas as pd
import numpy as np


def make_fec_df(n: int = 100, fiscal_year: int = 2024, include_tresorerie: bool = True) -> pd.DataFrame:
    """Génère un DataFrame FEC synthétique équilibré."""
    rng = np.random.default_rng(42)
    dates = pd.date_range(f"{fiscal_year}-01-01", f"{fiscal_year}-12-31", periods=n)
    amounts = rng.uniform(10_000, 5_000_000, n)

    compte_nums = []
    if include_tresorerie:
        pools = ["411000", "701000", "512000", "601000", "411100"]
    else:
        pools = ["411000", "701000", "601000", "411100", "401000"]

    for i in range(n):
        compte_nums.append(pools[i % len(pools)])

    return pd.DataFrame({
        "JournalCode": ["VT"] * n,
        "EcritureNum": [str(i) for i in range(1, n + 1)],
        "EcritureDate": dates,
        "CompteNum": compte_nums,
        "CompteLib": ["Compte divers"] * n,
        "EcritureLib": [f"Écriture {i}" for i in range(1, n + 1)],
        "Debit": [amt if i % 2 == 0 else 0.0 for i, amt in enumerate(amounts)],
        "Credit": [0.0 if i % 2 == 0 else amt for i, amt in enumerate(amounts)],
    })


@pytest.fixture
def fec_df():
    return make_fec_df()


@pytest.fixture
def fec_df_previous():
    """FEC de l'exercice N-1 avec valeurs légèrement différentes."""
    return make_fec_df(n=80, fiscal_year=2023)
