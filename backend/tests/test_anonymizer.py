"""Tests unitaires — Anonymiseur NLP"""
import pytest
from app.services.anonymizer import anonymize_text, anonymize_fec_dataframe
import pandas as pd


class TestAnonymizeText:
    def test_email_masked(self):
        text, count = anonymize_text("Contact: john.doe@cabinet.com pour suivi")
        assert "[EMAIL]" in text
        assert count > 0

    def test_phone_masked(self):
        text, count = anonymize_text("Tél: +226 70 12 34 56 pour confirmation")
        assert "[TEL]" in text

    def test_siret_masked(self):
        text, count = anonymize_text("SIRET 123 456 789 00012 société X")
        assert "[SIRET]" in text

    def test_empty_string(self):
        text, count = anonymize_text("")
        assert text == ""
        assert count == 0

    def test_no_sensitive_data(self):
        text, count = anonymize_text("Achat fournitures bureau 45000 FCFA")
        assert count == 0

    def test_multiple_patterns(self):
        text, count = anonymize_text("Email: admin@test.bf Tel: +226 75 00 00 00")
        assert count >= 2


class TestAnonymizeFecDataframe:
    def make_df(self):
        return pd.DataFrame({
            "CompteNum": ["411000", "701000"],
            "CompteLib": ["Clients", "Ventes"],
            "EcritureLib": ["Vente client john.doe@test.com", "Produit normal"],
            "Debit": [100000.0, 0.0],
            "Credit": [0.0, 100000.0],
        })

    def test_anonymizes_email_in_libelle(self):
        df, stats = anonymize_fec_dataframe(self.make_df())
        assert "[EMAIL]" in df["EcritureLib"].iloc[0]
        assert stats["total_substitutions"] > 0

    def test_numeric_columns_unchanged(self):
        df_orig = self.make_df()
        df_anon, _ = anonymize_fec_dataframe(df_orig)
        pd.testing.assert_series_equal(df_orig["Debit"], df_anon["Debit"])
        pd.testing.assert_series_equal(df_orig["Credit"], df_anon["Credit"])

    def test_returns_copy(self):
        df = self.make_df()
        df_anon, _ = anonymize_fec_dataframe(df)
        assert df is not df_anon
