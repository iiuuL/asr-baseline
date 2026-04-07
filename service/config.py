"""Service configuration placeholders.

This module intentionally stays small for now:
- it does not change current runtime behavior
- it gives `service.app` a future home for service-level settings
- it can be adopted incrementally without a large refactor
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceSettings:
    """Minimal service settings container.

    Future migration targets:
    - app title / version
    - host / port
    - CORS policy
    - default language / ITN flags
    - temp file behavior
    """

    app_title: str = "ASR Chunk Service"
    app_version: str = "1.0.0"
    default_language: str = "zh"
    default_use_itn: bool = True
    model_name: str = "iic/SenseVoiceSmall"
    health_status: str = "running"


def get_settings() -> ServiceSettings:
    """Return immutable default settings.

    Kept as a function so later we can switch to env-based loading
    without changing call sites.
    """

    return ServiceSettings()


__all__ = ["ServiceSettings", "get_settings"]
