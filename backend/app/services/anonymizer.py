"""
Anonymisation NLP des données nominatives avant traitement IA.
Masque : noms propres, SIRET/IFU, téléphones, emails, adresses.
"""
import re
from typing import Tuple
import pandas as pd


# Patterns regex robustes pour les données sensibles UEMOA/France
PATTERNS = [
    # Email
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    # Téléphone (formats UEMOA + international)
    (r'\b(?:\+226|\+225|\+221|\+237|\+33|00226|00225)?[\s.-]?(?:\d[\s.-]?){8,12}\b', '[TEL]'),
    # SIRET France (14 chiffres)
    (r'\b\d{3}[\s.-]?\d{3}[\s.-]?\d{3}[\s.-]?\d{5}\b', '[SIRET]'),
    # IFU Burkina (format 8-12 chiffres)
    (r'\bIFU\s*:?\s*\d{8,12}\b', '[IFU]'),
    (r'\b\d{8,12}[A-Z]\b', '[IFU]'),
    # RCCM
    (r'\bRCCM\s*[:\s]?\w{2,4}\d{4}[A-Z]\d+\b', '[RCCM]'),
    # Montants avec devises (ne pas anonymiser mais normaliser)
    # Noms propres : Majuscule + longueur (approximatif sans modèle NER)
    (r'\b([A-ZÉÀÈÊÎÔÙÛÜ][a-zéàèêîôùûü]{2,}\s){2,3}([A-ZÉÀÈÊÎÔÙÛÜ][a-zéàèêîôùûü]{2,})\b', '[NOM_PROPRE]'),
    # Adresses
    (r'\b\d{1,4}[,\s]+(?:rue|avenue|boulevard|av\.|bd\.|bp|B\.P\.|quartier|cité|secteur)[^,\n]{5,50}', '[ADRESSE]'),
    # Numéros de compte bancaire (format IBAN ou local)
    (r'\b[A-Z]{2}\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{0,4}\b', '[IBAN]'),
]

COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), repl) for p, repl in PATTERNS]


def anonymize_text(text: str) -> Tuple[str, int]:
    """
    Anonymise un texte libre.
    Retourne (texte_anonymisé, nombre_de_substitutions).
    """
    if not text:
        return text, 0

    total_subs = 0
    for pattern, replacement in COMPILED_PATTERNS:
        text, count = pattern.subn(replacement, text)
        total_subs += count

    return text, total_subs


def anonymize_fec_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Anonymise les colonnes textuelles d'un DataFrame FEC.
    Préserve les colonnes numériques et dates intactes.
    """
    df = df.copy()
    stats = {"columns_processed": [], "total_substitutions": 0}

    text_columns = [
        "CompteLib", "CompAuxLib", "EcritureLib", "PieceRef",
        "JournalLib", "EcritureLet",
    ]

    for col in text_columns:
        if col in df.columns:
            results = df[col].astype(str).apply(
                lambda x: anonymize_text(x) if x not in ("nan", "None", "") else (x, 0)
            )
            df[col] = results.apply(lambda x: x[0])
            subs = results.apply(lambda x: x[1]).sum()
            if subs > 0:
                stats["columns_processed"].append(col)
                stats["total_substitutions"] += int(subs)

    return df, stats


def anonymize_document_text(raw_text: str) -> Tuple[str, dict]:
    """
    Anonymise le texte extrait d'un PDF (liasse fiscale, bilan).
    """
    anonymized, count = anonymize_text(raw_text)
    return anonymized, {
        "original_length": len(raw_text),
        "anonymized_length": len(anonymized),
        "substitutions": count,
    }
