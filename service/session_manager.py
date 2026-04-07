"""In-memory session storage placeholder.

The current implementation in `service.app` keeps session bytes in
module-level globals. This file provides a small manager class so that
we can later move that logic out without changing endpoint behavior all
at once.
"""

from threading import Lock


class SessionStorageManager:
    """Thread-safe in-memory byte accumulator by session_id."""

    def __init__(self) -> None:
        self._storage: dict[str, bytearray] = {}
        self._lock = Lock()

    def append_chunk(self, session_id: str, content: bytes) -> bytes:
        """Append bytes to a session and return a snapshot of full audio."""

        with self._lock:
            if session_id not in self._storage:
                self._storage[session_id] = bytearray()
            self._storage[session_id].extend(content)
            return bytes(self._storage[session_id])

    def pop_session(self, session_id: str) -> None:
        """Delete a session if it exists."""

        with self._lock:
            self._storage.pop(session_id, None)

    def clear(self) -> None:
        """Clear all cached sessions."""

        with self._lock:
            self._storage.clear()

    def has_session(self, session_id: str) -> bool:
        """Check whether a session exists."""

        with self._lock:
            return session_id in self._storage

    def session_size(self, session_id: str) -> int:
        """Return cached byte length for a session."""

        with self._lock:
            data = self._storage.get(session_id)
            return 0 if data is None else len(data)


__all__ = ["SessionStorageManager"]
