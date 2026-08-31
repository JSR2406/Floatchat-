# Real-time marine data source adapters (INCOIS / IMD / MOSDAC).
# These wrap authoritative government marine data providers with clean
# typed interfaces. No fabricated fallbacks: an unconfigured source is reported
# as NOT_CONFIGURED, never silently replaced with mock data.
from app.datasources.base import BaseMarineDataSource  # noqa: F401
from app.datasources.errors import (  # noqa: F401
    SourceError,
    SourceInvalidDataError,
    SourceNotConfiguredError,
    SourceRateLimitError,
    SourceUnavailableError,
)
from app.datasources.http import HttpDataTransport  # noqa: F401
from app.datasources.imd import IMDAdapter  # noqa: F401
from app.datasources.incois import INCOISAdapter  # noqa: F401
from app.datasources.mosdac import MOSDACAdapter  # noqa: F401
from app.datasources.registry import SourceRegistry, build_registry  # noqa: F401