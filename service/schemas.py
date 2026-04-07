"""Shared schema placeholders for the service layer.

These types are not wired into the current FastAPI handlers yet.
They exist to make the response structure explicit before we migrate
`service.app` step by step.
"""

from typing import Any, Optional, TypedDict


class MetadataDict(TypedDict):
    """Normalized metadata shape returned by ASR endpoints."""

    language: Optional[str]
    emotion: Optional[str]
    events: list[str]
    has_speech: bool
    itn_mode: Optional[str]
    unknown_tags: list[str]


class HealthDataDict(TypedDict):
    """Suggested payload shape for the health endpoint."""

    status: str
    device: str
    model_loaded: bool
    model_name: str


class ChunkResultDict(TypedDict):
    """Suggested payload shape for `/asr/chunk` success responses."""

    session_id: str
    chunk_index: int
    is_final: bool
    text: str
    raw_text: str
    metadata: MetadataDict
    language: str
    device: str
    elapsed_ms: float
    filename: str


class ApiEnvelopeDict(TypedDict):
    """Suggested outer response envelope for future migration."""

    ok: bool
    code: str
    message: str
    data: Optional[dict[str, Any]]


def default_metadata() -> MetadataDict:
    """Return a stable empty metadata object."""

    return {
        "language": None,
        "emotion": None,
        "events": [],
        "has_speech": False,
        "itn_mode": None,
        "unknown_tags": [],
    }


def normalize_metadata(raw_metadata: Any) -> MetadataDict:
    """Normalize arbitrary metadata into the stable metadata shape.

    This mirrors the current logic in `service.app` so migration can be
    done by moving one function call at a time.
    """

    output = default_metadata()
    if isinstance(raw_metadata, dict):
        for key in output.keys():
            if key in raw_metadata:
                output[key] = raw_metadata[key]

    if not isinstance(output.get("events"), list):
        output["events"] = []

    return output


__all__ = [
    "ApiEnvelopeDict",
    "ChunkResultDict",
    "HealthDataDict",
    "MetadataDict",
    "default_metadata",
    "normalize_metadata",
]
