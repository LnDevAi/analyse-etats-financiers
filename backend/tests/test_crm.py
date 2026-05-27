"""Tests unitaires pour les schemas et la logique CRM."""
import pytest
from datetime import date
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.crm import (
    CRMClientCreate, CRMClientUpdate,
    CRMContactCreate, ActivityLogCreate,
)


# ── CRMClientCreate ───────────────────────────────────────────────────────────

class TestCRMClientCreate:
    def test_minimal_valid(self):
        c = CRMClientCreate(company_name="Mairie de Ouaga")
        assert c.company_name == "Mairie de Ouaga"
        assert c.country == "BF"
        assert c.lifecycle_status == "PROSPECT"
        assert c.pipeline_stage == "PROSPECT"

    def test_full_fields(self):
        c = CRMClientCreate(
            company_name="ONG AIDE",
            rccm="BF-OUA-2024-B-001",
            nif="123456789",
            sector="ONG",
            city="Bobo-Dioulasso",
            deal_value=150_000.0,
            expected_close_date=date(2026, 6, 30),
            source="Referral",
            tags=["ONG", "Audit"],
            lifecycle_status="TRIAL",
            pipeline_stage="QUALIFIÉ",
        )
        assert c.deal_value == 150_000.0
        assert c.tags == ["ONG", "Audit"]
        assert c.pipeline_stage == "QUALIFIÉ"

    def test_missing_company_name_raises(self):
        with pytest.raises(ValidationError):
            CRMClientCreate()

    def test_optional_tenant_id(self):
        c = CRMClientCreate(company_name="Test")
        assert c.tenant_id is None
        uid = uuid4()
        c2 = CRMClientCreate(company_name="Test", tenant_id=uid)
        assert c2.tenant_id == uid


# ── CRMClientUpdate ───────────────────────────────────────────────────────────

class TestCRMClientUpdate:
    def test_all_optional(self):
        u = CRMClientUpdate()
        assert u.company_name is None
        assert u.lifecycle_status is None

    def test_partial_update(self):
        u = CRMClientUpdate(pipeline_stage="GAGNÉ", health_score=85)
        assert u.pipeline_stage == "GAGNÉ"
        assert u.health_score == 85
        assert u.company_name is None

    def test_model_dump_excludes_none(self):
        u = CRMClientUpdate(lifecycle_status="ACTIF")
        dumped = u.model_dump(exclude_none=True)
        assert "lifecycle_status" in dumped
        assert "company_name" not in dumped


# ── CRMContactCreate ──────────────────────────────────────────────────────────

class TestCRMContactCreate:
    def test_valid_primary(self):
        c = CRMContactCreate(full_name="Moussa Kaboré", role="DAF", email="m@test.bf", is_primary=True)
        assert c.is_primary is True
        assert c.role == "DAF"

    def test_not_primary_by_default(self):
        c = CRMContactCreate(full_name="Alice")
        assert c.is_primary is False

    def test_optional_email_phone(self):
        c = CRMContactCreate(full_name="Bob")
        assert c.email is None
        assert c.phone is None

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            CRMContactCreate()


# ── ActivityLogCreate ─────────────────────────────────────────────────────────

class TestActivityLogCreate:
    def test_valid_call(self):
        a = ActivityLogCreate(
            activity_type="CALL",
            subject="Appel de qualification",
            duration_minutes=30,
            outcome="Intéressé",
        )
        assert a.activity_type == "CALL"
        assert a.duration_minutes == 30

    def test_all_optional_except_type(self):
        a = ActivityLogCreate(activity_type="NOTE")
        assert a.body is None
        assert a.next_action is None
        assert a.next_action_date is None

    def test_next_action_date_as_date(self):
        a = ActivityLogCreate(activity_type="EMAIL", next_action_date=date(2026, 6, 15))
        assert a.next_action_date == date(2026, 6, 15)

    def test_missing_type_raises(self):
        with pytest.raises(ValidationError):
            ActivityLogCreate()
