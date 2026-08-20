# Database Models
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, BigInteger, Float, String, DateTime, Text, Index, 
    ForeignKey, UniqueConstraint, JSON, ARRAY
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from geoalchemy2 import Geography


class Base(DeclarativeBase):
    pass


class ArgoProfile(Base):
    __tablename__ = "argo_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    platform_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    profile_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geom: Mapped[str] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qc_status: Mapped[str] = mapped_column(String(50), nullable=False, default="recommended")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    observations: Mapped[List["ArgoObservation"]] = relationship(back_populates="profile", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("platform_number", "cycle_number", name="uq_platform_cycle"),
        Index("idx_argo_profiles_geom", "geom", postgresql_using="gist"),
    )


class ArgoObservation(Base):
    __tablename__ = "argo_observations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("argo_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    pressure_dbar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depth_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salinity_psu: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oxygen_umol_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chlorophyll: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature_qc: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salinity_qc: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    oxygen_qc: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    profile: Mapped["ArgoProfile"] = relationship(back_populates="observations")

    __table_args__ = (
        Index("idx_argo_obs_profile", "profile_id"),
        Index("idx_argo_obs_temp", "temperature_c", postgresql_where="temperature_c IS NOT NULL"),
        Index("idx_argo_obs_salinity", "salinity_psu", postgresql_where="salinity_psu IS NOT NULL"),
    )


class DatasetSnapshot(Base):
    __tablename__ = "dataset_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dataset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str] = mapped_column(String(500), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    source_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    record_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    profile_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    float_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")


class QueryRun(Base):
    __tablename__ = "query_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    detected_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    normalized_intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    structured_query: Mapped[dict] = mapped_column(JSON, nullable=False)
    tool_calls: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    execution_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    evidence: Mapped[List["EvidenceRecord"]] = relationship(back_populates="query_run", cascade="all, delete-orphan")
    narratives: Mapped[List["Narrative"]] = relationship(back_populates="query_run", cascade="all, delete-orphan")
    scenarios: Mapped[List["ScenarioRun"]] = relationship(back_populates="query_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_query_runs_session_created", "session_id", "created_at"),
    )


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    query_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("query_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    float_ids: Mapped[List[int]] = mapped_column(ARRAY(Integer), nullable=False, default=[])
    profile_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    observation_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    region: Mapped[dict] = mapped_column(JSON, nullable=False)
    depth_range: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    time_range: Mapped[dict] = mapped_column(JSON, nullable=False)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False)
    data_freshness: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence_label: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_components: Mapped[dict] = mapped_column(JSON, nullable=False)
    limitations: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False, default=[])
    source_identifiers: Mapped[dict] = mapped_column(JSON, nullable=False)
    verified: Mapped[bool] = mapped_column(nullable=False, default=False)
    verification_errors: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    query_run: Mapped["QueryRun"] = relationship(back_populates="evidence")


class Narrative(Base):
    __tablename__ = "narratives"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    query_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("query_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    narrative_text: Mapped[str] = mapped_column(Text, nullable=False)
    numeric_claims: Mapped[List[dict]] = mapped_column(JSON, nullable=False, default=[])
    verified: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    query_run: Mapped["QueryRun"] = relationship(back_populates="narratives")


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    query_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("query_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    variable: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[dict] = mapped_column(JSON, nullable=False)
    baseline: Mapped[dict] = mapped_column(JSON, nullable=False)
    trend_window: Mapped[dict] = mapped_column(JSON, nullable=False)
    projection_horizon: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    assumptions: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False, default=[])
    uncertainty_method: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    query_run: Mapped["QueryRun"] = relationship(back_populates="scenarios")