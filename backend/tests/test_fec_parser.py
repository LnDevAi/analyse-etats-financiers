"""Tests unitaires — Parseur FEC"""
import pytest
import pandas as pd
from app.services.fec_parser import parse_fec, validate_partie_double

FEC_BALANCED = b"""JournalCode\tJournalLib\tEcritureNum\tEcritureDate\tCompteNum\tCompteLib\tCompAuxNum\tCompAuxLib\tPieceRef\tPieceDate\tEcritureLib\tDebit\tCredit\tEcritureLet\tDateLet\tValidDate\tMontantdevise\tIdevise
VT\tVentes\t1\t20240115\t701000\tVentes marchandises\t\t\tF001\t20240115\tVente client A\t0\t500000\t\t\t\t\t
VT\tVentes\t1\t20240115\t411000\tClients\t\t\tF001\t20240115\tVente client A\t500000\t0\t\t\t\t\t
"""

FEC_UNBALANCED = b"""JournalCode\tJournalLib\tEcritureNum\tEcritureDate\tCompteNum\tCompteLib\tCompAuxNum\tCompAuxLib\tPieceRef\tPieceDate\tEcritureLib\tDebit\tCredit\tEcritureLet\tDateLet\tValidDate\tMontantdevise\tIdevise
VT\tVentes\t1\t20240115\t701000\tVentes\t\t\tF001\t20240115\tVente\t0\t500000\t\t\t\t\t
VT\tVentes\t1\t20240115\t411000\tClients\t\t\tF001\t20240115\tVente\t600000\t0\t\t\t\t\t
"""


class TestFecParser:
    def test_parse_balanced(self):
        df, meta = parse_fec(FEC_BALANCED)
        assert len(df) == 2
        assert meta["rows"] == 2
        assert abs(meta["total_debit"] - meta["total_credit"]) < 0.01

    def test_parse_unbalanced(self):
        df, meta = parse_fec(FEC_UNBALANCED)
        assert abs(meta["total_debit"] - meta["total_credit"]) > 0

    def test_debit_credit_numeric(self):
        df, _ = parse_fec(FEC_BALANCED)
        assert df["Debit"].dtype == float
        assert df["Credit"].dtype == float

    def test_date_parsed(self):
        df, _ = parse_fec(FEC_BALANCED)
        assert pd.api.types.is_datetime64_any_dtype(df["EcritureDate"])

    def test_meta_keys(self):
        _, meta = parse_fec(FEC_BALANCED)
        assert "rows" in meta
        assert "total_debit" in meta
        assert "total_credit" in meta


class TestPartieDouble:
    def test_balanced(self):
        df, _ = parse_fec(FEC_BALANCED)
        result = validate_partie_double(df)
        assert result["valid"] is True
        assert result["difference"] < 0.01

    def test_unbalanced(self):
        df, _ = parse_fec(FEC_UNBALANCED)
        result = validate_partie_double(df)
        assert result["valid"] is False
        assert result["difference"] > 0

    def test_empty_df(self):
        df = pd.DataFrame({"Debit": [], "Credit": []})
        result = validate_partie_double(df)
        assert result["valid"] is True
