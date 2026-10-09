import pytest
import sqlite3
import json
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from geoalchemy2 import Geometry
from fastapi.testclient import TestClient

# Register sqlite3 adapters for python list and dict so SQLite can bind ARRAY and JSONB columns
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)

# Disable GeoAlchemy DDL events on SQLite so it doesn't try Spatialite table modifications
try:
    import geoalchemy2.admin.dialects.sqlite as _geo_sqlite
    _geo_sqlite.SQLiteDialect.after_create = lambda *args, **kwargs: None
    _geo_sqlite.SQLiteDialect.before_drop = lambda *args, **kwargs: None
    _geo_sqlite.create_spatial_index = lambda *args, **kwargs: None
    _geo_sqlite.disable_spatial_index = lambda *args, **kwargs: None
except (ImportError, AttributeError):
    pass


# ─── 1. SQLite Type Compilers for PostgreSQL-specific types ───────────────────
@compiles(ARRAY, "sqlite")
def compile_array(type_, compiler, **kw):
    return "TEXT"


@compiles(JSONB, "sqlite")
def compile_jsonb(type_, compiler, **kw):
    return "TEXT"


@compiles(Geometry, "sqlite")
def compile_geometry(type_, compiler, **kw):
    return "TEXT"


# ─── 2. In-Memory SQLite Test Engine ──────────────────────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def register_sqlite_spatial_stubs(dbapi_connection, connection_record):
    def echo_arg(*args):
        return args[0] if args else None

    def dummy_func(*args):
        return 1

    spatial_funcs = [
        "RecoverGeometryColumn",
        "AddGeometryColumn",
        "DiscardGeometryColumn",
        "CreateSpatialIndex",
        "DisableSpatialIndex",
        "CheckSpatialIndex",
        "InitSpatialMetaData",
        "CheckSpatialMetaData",
    ]
    for func_name in spatial_funcs:
        dbapi_connection.create_function(func_name, -1, dummy_func)

    # Transform / Conversion spatial functions (return first arg or None)
    transform_funcs = [
        "GeomFromEWKT",
        "GeomFromText",
        "GeomFromWKB",
        "ST_GeomFromText",
        "ST_GeomFromWKB",
        "ST_GeomFromEWKT",
        "AsEWKB",
        "AsText",
        "ST_AsText",
        "ST_AsBinary",
        "ST_AsGeoJSON",
    ]
    for func_name in transform_funcs:
        dbapi_connection.create_function(func_name, -1, echo_arg)


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ─── 3. Patch app.database BEFORE importing app.main ─────────────────────────
import app.database as app_db

app_db.engine = test_engine
app_db.SessionLocal = TestingSessionLocal

from app.database import Base, get_db
from app.main import app
from app.config import get_settings
from app.eo_gateway.registry import init_registry


@pytest.fixture(scope="session", autouse=True)
def init_app_state():
    settings = get_settings()
    init_registry(settings)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
