"""Phase 4 — Add EO pipeline columns to satellite_scenes.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── New columns on satellite_scenes ──────────────────────────────────────

    # Extend scene_id to 256 characters for longer provider IDs
    op.alter_column(
        "satellite_scenes",
        "scene_id",
        type_=sa.String(256),
        existing_type=sa.String(128),
        existing_nullable=False,
    )

    # Provider identity
    op.add_column(
        "satellite_scenes",
        sa.Column("provider", sa.String(64), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "satellite_scenes",
        sa.Column("satellite", sa.String(128), nullable=True),
    )
    op.add_column(
        "satellite_scenes",
        sa.Column("resolution_m", sa.Float(), nullable=True),
    )

    # Spatial bounding box (denormalized for fast queries)
    op.add_column("satellite_scenes", sa.Column("bbox_min_lon", sa.Float(), nullable=True))
    op.add_column("satellite_scenes", sa.Column("bbox_min_lat", sa.Float(), nullable=True))
    op.add_column("satellite_scenes", sa.Column("bbox_max_lon", sa.Float(), nullable=True))
    op.add_column("satellite_scenes", sa.Column("bbox_max_lat", sa.Float(), nullable=True))

    # Raster file storage
    op.add_column("satellite_scenes", sa.Column("file_path", sa.Text(), nullable=True))
    op.add_column("satellite_scenes", sa.Column("file_size_bytes", sa.BigInteger(), nullable=True))
    op.add_column("satellite_scenes", sa.Column("crs", sa.String(64), nullable=True))
    op.add_column(
        "satellite_scenes",
        sa.Column("bands", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Provenance & source
    op.add_column("satellite_scenes", sa.Column("source_url", sa.Text(), nullable=True))
    op.add_column(
        "satellite_scenes",
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Ingestion lifecycle
    op.add_column(
        "satellite_scenes",
        sa.Column(
            "ingestion_status",
            sa.String(16),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column("satellite_scenes", sa.Column("ingestion_error", sa.Text(), nullable=True))
    op.add_column(
        "satellite_scenes",
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── New indexes ────────────────────────────────────────────────────────────
    op.create_index(
        "ix_satellite_scenes_provider_scene_id",
        "satellite_scenes",
        ["provider", "scene_id"],
    )
    op.create_index(
        "ix_satellite_scenes_provider",
        "satellite_scenes",
        ["provider"],
    )
    op.create_index(
        "ix_satellite_scenes_ingestion_status",
        "satellite_scenes",
        ["ingestion_status"],
    )
    op.create_index(
        "ix_satellite_scenes_acq_date",
        "satellite_scenes",
        ["acquisition_date"],
    )
    op.create_index(
        "ix_satellite_scenes_satellite",
        "satellite_scenes",
        ["satellite"],
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_satellite_scenes_satellite", table_name="satellite_scenes")
    op.drop_index("ix_satellite_scenes_acq_date", table_name="satellite_scenes")
    op.drop_index("ix_satellite_scenes_ingestion_status", table_name="satellite_scenes")
    op.drop_index("ix_satellite_scenes_provider", table_name="satellite_scenes")
    op.drop_index("ix_satellite_scenes_provider_scene_id", table_name="satellite_scenes")

    # Drop columns
    for col in [
        "ingested_at", "ingestion_error", "ingestion_status",
        "provenance", "source_url",
        "bands", "crs", "file_size_bytes", "file_path",
        "bbox_max_lat", "bbox_max_lon", "bbox_min_lat", "bbox_min_lon",
        "resolution_m", "satellite", "provider",
    ]:
        op.drop_column("satellite_scenes", col)

    # Revert scene_id length
    op.alter_column(
        "satellite_scenes",
        "scene_id",
        type_=sa.String(128),
        existing_type=sa.String(256),
        existing_nullable=False,
    )
