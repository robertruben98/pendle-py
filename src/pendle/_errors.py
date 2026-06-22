"""Exception hierarchy for the Pendle client."""

from __future__ import annotations

from typing import Optional


class PendleError(Exception):
    """Base class for all errors raised by this library.

    Catch this to handle any failure originating from ``pendle`` (currently just
    :class:`PendleAPIError`). Network-level failures from the underlying
    ``httpx`` client propagate as ``httpx`` exceptions and are not wrapped.
    """


class PendleAPIError(PendleError):
    """Raised when the Pendle API returns an error response.

    The Pendle API signals errors with a non-2xx HTTP status and a JSON body of
    the shape ``{"message", "error", "statusCode"}`` (e.g.
    ``400 "Invalid receiver address"`` or ``404 "Not Found"``).

    Attributes:
        message: The API's ``message`` text, falling back to ``"HTTP <status>"``.
        error: The API's short ``error`` label (e.g. ``"Bad Request"``,
            ``"Not Found"``), or ``None`` if absent.
        status_code: The HTTP status code of the response.

    Example::

        from pendle import PendleClient, PendleAPIError

        with PendleClient() as client:
            try:
                client.get_market(1, "0xnot-a-market")
            except PendleAPIError as exc:
                print(exc.status_code, exc.message)  # 404 'Not Found'
    """

    def __init__(
        self,
        *,
        message: str,
        status_code: int,
        error: Optional[str] = None,
    ) -> None:
        self.message = message
        self.error = error
        self.status_code = status_code
        super().__init__(f"[HTTP {status_code}] {message}")
