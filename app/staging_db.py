# app/staging_db.py

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

StagingBase = declarative_base()
_staging_engine = None
StagingSession = None


def init_staging_db(app):
    """
    Call this once during app startup (in create_app).
    Creates the engine connected to rro_staging database.
    """
    global _staging_engine, StagingSession

    uri = app.config["STAGING_DATABASE_URI"]
    _staging_engine = create_engine(uri, pool_pre_ping=True)
    StagingSession = sessionmaker(bind=_staging_engine)

    # Create tables in rro_staging if they don't exist yet
    StagingBase.metadata.create_all(_staging_engine)
    print("[StagingDB] Connected and tables ensured.")


def get_staging_session():
    """Returns a new session for the staging database."""
    return StagingSession()