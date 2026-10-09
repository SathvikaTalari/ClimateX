"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-08-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension first
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ── roles ──────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roles_id", "roles", ["id"])
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── user_roles ─────────────────────────────────────────────────────────
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    # ── environmental_domains ──────────────────────────────────────────────
    op.create_table(
        "environmental_domains",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("icon_name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="Monitoring"),
        sa.Column("key_indicator", sa.String(length=128), nullable=False),
        sa.Column("indicator_value", sa.String(length=64), nullable=False),
        sa.Column("change_rate", sa.String(length=32), nullable=False),
        sa.Column("primary_risk", sa.String(length=255), nullable=False),
        sa.Column("affected_regions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('Stable', 'Vulnerable', 'Critical Risk', 'Monitoring')",
            name="ck_domain_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_environmental_domains_id", "environmental_domains", ["id"])

    # ── administrative_areas ───────────────────────────────────────────────
    op.create_table(
        "administrative_areas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("country", sa.String(length=128), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("geometry", Geometry("MULTIPOLYGON", srid=4326), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_administrative_areas_id", "administrative_areas", ["id"])
    op.create_index("ix_administrative_areas_name", "administrative_areas", ["name"])
    op.create_index("ix_administrative_areas_country", "administrative_areas", ["country"])

    # ── locations ──────────────────────────────────────────────────────────
    op.create_table(
        "locations",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=128), nullable=False),
        sa.Column("country", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("zoom", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("landform", sa.String(length=255), nullable=False),
        sa.Column("elevation", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.String(length=16), nullable=False, server_default="Moderate"),
        sa.Column("satellite_sensors", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("last_observation", sa.String(length=64), nullable=True),
        sa.Column("geometry", Geometry("POINT", srid=4326), nullable=True),
        sa.Column(
            "dominant_domain_id",
            sa.String(length=64),
            sa.ForeignKey("environmental_domains.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "administrative_area_id",
            sa.Integer(),
            sa.ForeignKey("administrative_areas.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "risk_level IN ('Low', 'Moderate', 'High', 'Severe')",
            name="ck_location_risk_level",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_locations_id", "locations", ["id"])
    op.create_index("ix_locations_name", "locations", ["name"])
    op.create_index("ix_locations_dominant_domain_id", "locations", ["dominant_domain_id"])
    op.create_index("ix_locations_geometry", "locations", ["geometry"], postgresql_using="gist")

    # ── location_key_stats ─────────────────────────────────────────────────
    op.create_table(
        "location_key_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "location_id",
            sa.String(length=32),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("value", sa.String(length=64), nullable=False),
        sa.Column("trend", sa.String(length=16), nullable=False, server_default="stable"),
        sa.CheckConstraint("trend IN ('up', 'down', 'stable')", name="ck_key_stat_trend"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_location_key_stats_id", "location_key_stats", ["id"])
    op.create_index("ix_location_key_stats_location_id", "location_key_stats", ["location_id"])

    # ── datasets ───────────────────────────────────────────────────────────
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("data_type", sa.String(length=64), nullable=True),
        sa.Column("resolution", sa.String(length=64), nullable=True),
        sa.Column("temporal_coverage", sa.String(length=128), nullable=True),
        sa.Column(
            "domain_id",
            sa.String(length=64),
            sa.ForeignKey("environmental_domains.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "location_id",
            sa.String(length=32),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "data_type IN ('raster', 'vector', 'tabular', 'point_cloud', 'time_series', 'other')",
            name="ck_dataset_data_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_datasets_id", "datasets", ["id"])
    op.create_index("ix_datasets_name", "datasets", ["name"])
    op.create_index("ix_datasets_domain_id", "datasets", ["domain_id"])
    op.create_index("ix_datasets_location_id", "datasets", ["location_id"])

    # ── satellite_scenes ───────────────────────────────────────────────────
    op.create_table(
        "satellite_scenes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scene_id", sa.String(length=128), nullable=False),
        sa.Column("sensor", sa.String(length=128), nullable=False),
        sa.Column("acquisition_date", sa.Date(), nullable=False),
        sa.Column("cloud_cover", sa.Float(), nullable=True),
        sa.Column("footprint", Geometry("POLYGON", srid=4326), nullable=True),
        sa.Column("scene_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "location_id",
            sa.String(length=32),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "domain_id",
            sa.String(length=64),
            sa.ForeignKey("environmental_domains.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_satellite_scenes_id", "satellite_scenes", ["id"])
    op.create_index("ix_satellite_scenes_scene_id", "satellite_scenes", ["scene_id"], unique=True)
    op.create_index("ix_satellite_scenes_sensor", "satellite_scenes", ["sensor"])
    op.create_index("ix_satellite_scenes_acquisition_date", "satellite_scenes", ["acquisition_date"])
    op.create_index("ix_satellite_scenes_location_id", "satellite_scenes", ["location_id"])
    op.create_index("ix_satellite_scenes_domain_id", "satellite_scenes", ["domain_id"])
    op.create_index("ix_satellite_scenes_footprint", "satellite_scenes", ["footprint"], postgresql_using="gist")

    # ── observations ───────────────────────────────────────────────────────
    op.create_table(
        "observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metric_name", sa.String(length=128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("trend", sa.String(length=16), nullable=True, server_default="stable"),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("geometry", Geometry("POINT", srid=4326), nullable=True),
        sa.Column(
            "location_id",
            sa.String(length=32),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "domain_id",
            sa.String(length=64),
            sa.ForeignKey("environmental_domains.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "scene_id",
            sa.Integer(),
            sa.ForeignKey("satellite_scenes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("trend IN ('up', 'down', 'stable')", name="ck_observation_trend"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_observations_id", "observations", ["id"])
    op.create_index("ix_observations_metric_name", "observations", ["metric_name"])
    op.create_index("ix_observations_observed_at", "observations", ["observed_at"])
    op.create_index("ix_observations_location_id", "observations", ["location_id"])
    op.create_index("ix_observations_domain_id", "observations", ["domain_id"])
    op.create_index("ix_observations_scene_id", "observations", ["scene_id"])
    op.create_index("ix_observations_location_time", "observations", ["location_id", "observed_at"])
    op.create_index("ix_observations_domain_time", "observations", ["domain_id", "observed_at"])
    op.create_index("ix_observations_geometry", "observations", ["geometry"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_table("observations")
    op.drop_table("satellite_scenes")
    op.drop_table("datasets")
    op.drop_table("location_key_stats")
    op.drop_table("locations")
    op.drop_table("administrative_areas")
    op.drop_table("environmental_domains")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
