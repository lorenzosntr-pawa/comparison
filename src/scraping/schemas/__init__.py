"""Scraping schemas subpackage.

Re-exports from both the coordinator module and the parent schemas module
to maintain backward compatibility with imports like:
  from src.scraping.schemas import Platform, PlatformResult
"""

# Coordinator-specific schemas (event-centric architecture)
from src.scraping.schemas.coordinator import EventTarget, ScrapeBatch, ScrapeStatus

# Import parent schemas module and re-export common types
# This handles the case where schemas/ directory shadows schemas.py
import importlib.util
import sys
from pathlib import Path

# Load the parent schemas.py directly since it's shadowed by this package
_parent_schemas_path = Path(__file__).parent.parent / "schemas.py"
_spec = importlib.util.spec_from_file_location("_parent_schemas", _parent_schemas_path)
_parent_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parent_module)

# Re-export from parent schemas.py
Platform = _parent_module.Platform
PlatformResult = _parent_module.PlatformResult
ScrapePhase = _parent_module.ScrapePhase
PlatformStatus = _parent_module.PlatformStatus
ScrapeProgress = _parent_module.ScrapeProgress
ScrapeResult = _parent_module.ScrapeResult
ScrapeErrorContext = _parent_module.ScrapeErrorContext

__all__ = [
    # Coordinator schemas
    "EventTarget",
    "ScrapeBatch",
    "ScrapeStatus",
    # Parent schemas (Platform, etc.)
    "Platform",
    "PlatformResult",
    "ScrapePhase",
    "PlatformStatus",
    "ScrapeProgress",
    "ScrapeResult",
    "ScrapeErrorContext",
]
