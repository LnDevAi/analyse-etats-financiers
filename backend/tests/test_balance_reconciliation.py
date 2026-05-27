"""Tests unitaires — Réconciliation Balance Générale ↔ FEC"""
import pytest
import pandas as pd
from app.services.balance_reconciliation import (
    parse_balance_generale,
    run_balance_reconciliation,
)


def make_fec_df(accounts: dict) -> pd.DataFrame:
    """accounts: {compte_num: (total_debit, total_credit)}"""
    rows = []
    for compte, (debit, credit) in accounts.items():
        if debit > 0:
            rows.append({"CompteNum": compte, "Debit": debit, "Credit": 0.0, "EcritureLib": "Écriture", "EcritureDate": "2024-01-15"})
        if credit > 0:
            rows.append({"CompteNum": compte, "Debit": 0.0, "Credit": credit, "EcritureLib": "Écriture", "EcritureDate": "2024-01-15"})
    return pd.DataFrame(rows)


def make_balance_csv(accounts: dict, sep: str = "\t") -> bytes:
    """accounts: {compte_num: (total_debit, total_credit)}"""
    lines = ["CompteNum\tCompteLib\tDebit\tCredit"]
    for compte, (debit, credit) in accounts.items():
        lines.append(f"{compte}\tCompte {compte}\t{debit}\t{credit}")
    return "\n".join(lines).encode("utf-8")


ACCOUNTS_FEC = {
    "411000": (5_000_000, 0),
    "701000": (0, 5_000_000),
    "512000": (3_000_000, 2_000_000),
    "601000": (1_200_000, 0),
}


class TestParseBalanceGenerale:
    def test_tab_separated(self):
        content = make_balance_csv(ACCOUNTS_FEC)
        result = parse_balance_generale(content)
        assert "error" not in result
        assert result["rows"] == len(ACCOUNTS_FEC)
        assert result["total_debit"] > 0

    def test_semicolon_separated(self):
        lines = ["CompteNum;CompteLib;Debit;Credit"]
        lines.append("411000;Clients;5000000;0")
        content = ";".join(["411000", "Clients", "5000000", "0"])
        full = "CompteNum;CompteLib;Debit;Credit\n411000;Clients;5000000;0"
        result = parse_balance_generale(full.encode("utf-8"))
        assert "error" not in result
        assert result["rows"] == 1

    def test_missing_account_column(self):
        content = b"Libelle\tDebit\tCredit\nVentes\t0\t5000000"
        result = parse_balance_generale(content)
        assert "error" in result

    def test_comma_as_decimal_separator(self):
        content = "CompteNum\tCompteLib\tDebit\tCredit\n701000\tVentes\t0\t5 000 000".encode()
        result = parse_balance_generale(content)
        assert "error" not in result

    def test_numeric_filtering(self):
        """Les comptes non-numériques (totaux, sous-titres) doivent être ignorés."""
        content = (
            "CompteNum\tCompteLib\tDebit\tCredit\n"
            "411000\tClients\t5000000\t0\n"
            "TOTAL\tTotal général\t5000000\t0\n"
        ).encode()
        result = parse_balance_generale(content)
        assert result["rows"] == 1  # TOTAL filtré


class TestRunBalanceReconciliation:
    def test_perfect_match(self):
        df_fec = make_fec_df(ACCOUNTS_FEC)
        balance_content = make_balance_csv(ACCOUNTS_FEC)
        result = run_balance_reconciliation(df_fec, balance_content)
        assert result["discrepancies_count"] == 0
        assert result["risk_level"] == "VERT"

    def test_missing_account_in_balance(self):
        """Compte présent dans FEC mais absent de la balance → ABSENT_BALANCE."""
        df_fec = make_fec_df({"411000": (5_000_000, 0), "699000": (500_000, 0)})
        balance_content = make_balance_csv({"411000": (5_000_000, 0)})
        result = run_balance_reconciliation(df_fec, balance_content)
        absent = [d for d in result["discrepancies"] if d["flag"] == "ABSENT_BALANCE"]
        assert len(absent) >= 1
        assert any(d["account"] == "699000" for d in absent)

    def test_account_absent_in_fec(self):
        """Compte dans balance mais absent FEC → ABSENT_FEC."""
        df_fec = make_fec_df({"411000": (5_000_000, 0)})
        balance_content = make_balance_csv({
            "411000": (5_000_000, 0),
            "501000": (2_000_000, 0),  # Absent du FEC
        })
        result = run_balance_reconciliation(df_fec, balance_content)
        absent = [d for d in result["discrepancies"] if d["flag"] == "ABSENT_FEC"]
        assert len(absent) >= 1

    def test_solde_discrepancy(self):
        """Même compte mais montants différents → écart de solde."""
        df_fec = make_fec_df({"411000": (5_000_000, 0)})
        balance_content = make_balance_csv({"411000": (4_000_000, 0)})  # 1M de différence
        result = run_balance_reconciliation(df_fec, balance_content)
        assert result["discrepancies_count"] >= 1
        assert result["discrepancies"][0]["ecart_solde"] > 0

    def test_inversion_debit_credit(self):
        """Débit et crédit inversés entre FEC et balance → ROUGE."""
        df_fec = make_fec_df({"701000": (0, 5_000_000)})
        balance_content = make_balance_csv({"701000": (5_000_000, 0)})
        result = run_balance_reconciliation(df_fec, balance_content)
        inv = [d for d in result["discrepancies"] if d["flag"] == "INVERSION_DEBIT_CREDIT"]
        assert len(inv) >= 1
        assert inv[0]["severity"] == "ROUGE"

    def test_rouge_risk_level(self):
        """Écart majeur → risk_level ROUGE."""
        df_fec = make_fec_df({"411000": (10_000_000, 0)})
        balance_content = make_balance_csv({"411000": (1_000_000, 0)})
        result = run_balance_reconciliation(df_fec, balance_content)
        assert result["risk_level"] == "ROUGE"

    def test_missing_fec_column(self):
        df = pd.DataFrame({"Debit": [100.0]})
        result = run_balance_reconciliation(df, b"CompteNum\tDebit\n411000\t100")
        assert "error" in result

    def test_interpretation_present(self):
        df_fec = make_fec_df(ACCOUNTS_FEC)
        balance_content = make_balance_csv(ACCOUNTS_FEC)
        result = run_balance_reconciliation(df_fec, balance_content)
        assert "interpretation" in result
        assert len(result["interpretation"]) > 10

    def test_summary_structure(self):
        df_fec = make_fec_df(ACCOUNTS_FEC)
        balance_content = make_balance_csv(ACCOUNTS_FEC)
        result = run_balance_reconciliation(df_fec, balance_content)
        assert "fec_summary" in result
        assert "balance_summary" in result
        assert "accounts_compared" in result
