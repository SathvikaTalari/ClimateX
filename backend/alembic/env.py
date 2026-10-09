import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the backend directory to sys.path so app package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
from app.config import get_settings

# Import all models to register them with Base.metadata
from app.models import (  # noqa: F401
    User, Role, user_roles,
    EnvironmentalDomain,
    AdministrativeArea, Location, LocationKeyStat,
    Dataset,
    SatelliteScene,
    Observation,
    ProcessedImage, SpatialFeature,
)

config = context.config
settings = get_settings()

# Override the sqlalchemy.url from .env
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in {
        "spatial_ref_sys", "topology", "layer", "featnames", "zip_lookup_base", "zip_lookup",
        "county", "pagc_rules", "tabblock", "geocode_settings_default", "street_type_lookup", "state", "zip_lookup_all",
        "pagc_lex", "pagc_gaz", "loader_lookuptables", "addrfeat", "cousub", "loader_variables", "edges", "zip_state",
        "loader_platform", "geocode_settings", "bg", "place", "state_lookup", "zip_state_loc", "addr", "zcta5",
        "place_lookup", "direction_lookup", "county_lookup", "secondary_unit_lookup", "faces", "tract", "countysub_lookup", "tabblock20"
    }:
        return False
    return True

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_object=include_object,
            user_module_prefix="sa."
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
