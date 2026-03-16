# app/models/staged_bug.py

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.staging_db import StagingBase


class StagedBug(StagingBase):
    """
    Temporary table in rro_staging.
    Stores raw bug data fetched from the external API on every login.
    This table is CLEARED and REFILLED on each login.
    """
    __tablename__ = "staged_bugs"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    bug_code       = Column(String(50), unique=True, nullable=False)
    product        = Column(String(100))
    component      = Column(String(100))
    status         = Column(String(50))
    assignee       = Column(String(150))
    reporter       = Column(String(150))
    priority       = Column(String(10))
    severity       = Column(String(50))
    build_version  = Column(String(50))
    summary        = Column(Text)
    comments_json  = Column(Text)   # stores all comments as a JSON string
    fetched_at     = Column(DateTime, server_default=func.now())