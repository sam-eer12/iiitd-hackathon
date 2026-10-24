"""Declarative base and shared metadata for tenderlens_api schema."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Dedicated PostgreSQL schema for TenderLens API tables
metadata_obj = MetaData(schema="tenderlens_api")


class Base(DeclarativeBase):
    metadata = metadata_obj
