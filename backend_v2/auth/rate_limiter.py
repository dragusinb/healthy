"""
Simple in-memory rate limiter for authentication endpoints.
For production with multiple workers, use Redis-based rate limiting.
"""
import time
from collections import defaultdict
from threading import Lock
from fastapi import HTTPException, Request
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_LOGIN_ATTEMPTS = 5  # Max attempts per window
LOGIN_WINDOW_SECONDS = 300  # 5 minute window
LOCKOUT_SECONDS = 900  # 15 minute lockout after max attempts

MAX_REGISTER_ATTEMPTS = 3  # Max registrations per window
REGISTER_WINDOW_SECONDS = 3600  # 1 hour window


class RateLimiter:
    """Thread-safe in-memory rate limiter."""

    def __init__(self):
        self._attempts = defaultdict(list)  # key -> list of timestamps
        self._lockouts = {}  # key -> lockout_until timestamp
        self._lock = Lock()

    def _cleanup_old_attempts(self, key: str, window_seconds: int):
        """Remove attempts older than the window."""
        cutoff = time.time() - window_seconds
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]

    def _is_locked_out(self, key: str) -> bool:
        """Check if key is currently locked out."""
        if key in self._lockouts:
            if time.time() < self._lockouts[key]:
                return True
            else:
                # Lockout expired, remove it
                del self._lockouts[key]
        return False

    def check_rate_limit(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int,
        lockout_seconds: int = 0
    ) -> bool:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier (e.g., IP address, email)
            max_attempts: Maximum attempts allowed in window
            window_seconds: Time window in seconds
            lockout_seconds: If > 0, lock out for this many seconds after max attempts

        Returns:
            True if request is allowed, raises HTTPException if rate limited
        """
        with self._lock:
            # Check if locked out
            if self._is_locked_out(key):
                remaining = int(self._lockouts[key] - time.time())
                logger.warning(f"Rate limit lockout for {key}, {remaining}s remaining")
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many attempts. Please try again in {remaining} seconds.",
                    headers={"Retry-After": str(remaining)}
                )

            # Cleanup old attempts
            self._cleanup_old_attempts(key, window_seconds)

            # Check current attempts
            current_attempts = len(self._attempts[key])

            if current_attempts >= max_attempts:
                # Apply lockout if configured
                if lockout_seconds > 0:
                    self._lockouts[key] = time.time() + lockout_seconds
                    logger.warning(f"Rate limit exceeded for {key}, locked out for {lockout_seconds}s")
                    raise HTTPException(
                        status_code=429,
                        detail=f"Too many attempts. Please try again in {lockout_seconds} seconds.",
                        headers={"Retry-After": str(lockout_seconds)}
                    )
                else:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests. Please slow down.",
                        headers={"Retry-After": str(window_seconds)}
                    )

            # Record this attempt
            self._attempts[key].append(time.time())
            return True

    def reset(self, key: str):
        """Reset rate limit for a key (e.g., after successful login)."""
        with self._lock:
            if key in self._attempts:
                del self._attempts[key]
            if key in self._lockouts:
                del self._lockouts[key]


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded header (behind reverse proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP (original client)
        return forwarded.split(",")[0].strip()
    # Fall back to direct connection
    return request.client.host if request.client else "unknown"


def check_login_rate_limit(request: Request):
    """
    Rate limit dependency for login endpoint.
    Limits by IP address.
    """
    client_ip = get_client_ip(request)
    _rate_limiter.check_rate_limit(
        key=f"login:{client_ip}",
        max_attempts=MAX_LOGIN_ATTEMPTS,
        window_seconds=LOGIN_WINDOW_SECONDS,
        lockout_seconds=LOCKOUT_SECONDS
    )


def check_register_rate_limit(request: Request):
    """
    Rate limit dependency for registration endpoint.
    Limits by IP address.
    """
    client_ip = get_client_ip(request)
    _rate_limiter.check_rate_limit(
        key=f"register:{client_ip}",
        max_attempts=MAX_REGISTER_ATTEMPTS,
        window_seconds=REGISTER_WINDOW_SECONDS,
        lockout_seconds=0  # No lockout for registration, just slow down
    )


def reset_login_rate_limit(request: Request):
    """Reset login rate limit after successful login."""
    client_ip = get_client_ip(request)
    _rate_limiter.reset(f"login:{client_ip}")
