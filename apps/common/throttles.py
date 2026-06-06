from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Strict per-IP limit on login attempts to slow down brute-force attacks.

    Rate is configured via DEFAULT_THROTTLE_RATES["login"] in settings.py.
    Default: 5/minute.
    """

    scope = "login"


class BurstRateThrottle(UserRateThrottle):
    """Short-window burst limit for authenticated users (e.g. rapid API calls)."""

    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    """Long-window sustained limit for authenticated users (daily cap)."""

    scope = "sustained"
