# Datasets Router
# Dataset status endpoint

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.config import settings
from app.db.client import get_db_session
from app.db.models import DatasetSnapshot
from app.data.cache import get_cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.get("/status")
async def dataset_status(session: AsyncSession = Depends(get_db_session)):
    """Get status of available datasets."""
    datasets = []
    
    # Check database for snapshots
    stmt = select(DatasetSnapshot).where(DatasetSnapshot.status == "active")
    result = await session.execute(stmt)
    snapshots = result.scalars().all()
    
    for snap in snapshots:
        datasets.append({
            "name": snap.dataset_name,
            "region": snap.region,
            "start_time": snap.start_time.isoformat() if snap.start_time else None,
            "end_time": snap.end_time.isoformat() if snap.end_time else None,
            "source": snap.source,
            "source_version": snap.source_version,
            "record_count": snap.record_count,
            "profile_count": snap.profile_count,
            "float_count": snap.float_count,
            "ingested_at": snap.ingested_at.isoformat() if snap.ingested_at else None,
            "status": snap.status,
            "checksum": snap.checksum,
        })
    
    # Check cache for demo data
    cache = get_cache_manager()
    manifest = cache.load_manifest()
    
    if manifest:
        datasets.append({
            "name": manifest.get("dataset_name", "demo"),
            "region": manifest.get("region", "Unknown"),
            "start_time": manifest.get("start_time"),
            "end_time": manifest.get("end_time"),
            "source": manifest.get("source", "Demo data"),
            "source_version": manifest.get("source_version", "demo"),
            "record_count": manifest.get("record_count", 0),
            "profile_count": manifest.get("profile_count", 0),
            "float_count": manifest.get("float_count", 0),
            "ingested_at": manifest.get("ingested_at"),
            "status": manifest.get("status", "active"),
            "checksum": manifest.get("checksum"),
            "demo_mode": True,
        })
    
    return {
        "datasets": datasets,
        "demo_mode": settings.demo_mode,
    }