"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.Enum('CABINET_EXPERTISE', 'ADMINISTRATION_FISCALE', 'BANQUE', name='tenanttype'), nullable=False),
        sa.Column('siret', sa.String(50), nullable=True),
        sa.Column('email_contact', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('schema_name', sa.String(63), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('schema_name'),
    )

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('ASSOCIE', 'CHEF_MISSION', 'AUDITEUR_JUNIOR', name='userrole'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('mfa_secret', sa.String(64), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('storage_path', sa.String(512), nullable=False),
        sa.Column('document_type', sa.Enum('FEC', 'LIASSE_FISCALE_PDF', 'BILAN_PDF', 'AUTRE', name='documenttype'), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('status', sa.Enum('UPLOADED', 'PROCESSING', 'OCR_DONE', 'ANONYMIZED', 'READY', 'ERROR', name='documentstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('fiscal_year', sa.Integer(), nullable=True),
        sa.Column('entity_name', sa.String(255), nullable=True),
        sa.Column('is_anonymized', sa.Boolean(), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_documents_tenant_id', 'documents', ['tenant_id'])

    op.create_table(
        'analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('triggered_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', name='analysisstatus'), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.Enum('VERT', 'ORANGE', 'ROUGE', name='risklevel'), nullable=True),
        sa.Column('intrinsic_check', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('benford_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('isolation_forest_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cross_check_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('analytical_review', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cycle_ventes_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cycle_tresorerie_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_synthesis', sa.Text(), nullable=True),
        sa.Column('ai_report_general', sa.Text(), nullable=True),
        sa.Column('docx_report_path', sa.String(512), nullable=True),
        sa.Column('xlsx_report_path', sa.String(512), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_analyses_tenant_id', 'analyses', ['tenant_id'])

    op.create_table(
        'anomalies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('module', sa.String(100), nullable=False),
        sa.Column('severity', sa.Enum('VERT', 'ORANGE', 'ROUGE', name='risklevel'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_account', sa.String(50), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_anomalies_analysis_id', 'anomalies', ['analysis_id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result', sa.String(20), nullable=False, server_default='SUCCESS'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('anomalies')
    op.drop_table('analyses')
    op.drop_table('documents')
    op.drop_table('users')
    op.drop_table('tenants')
