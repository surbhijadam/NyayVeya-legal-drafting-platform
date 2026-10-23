"""
Security and privacy hardening module for NyayVeya (Phase 8).

Provides:
1. HTTP Security Headers (Content-Security-Policy, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
2. Secure Session & Cookie Configurations
3. In-memory sliding-window Rate Limiting for sensitive endpoints (Brute-force & DoS mitigation)
4. Private file isolation guarantees and DPDP Act / Privacy alignment
"""
import os
import time
import threading
from functools import wraps
from datetime import timedelta
from typing import Optional
from flask import (
    request, jsonify, render_template, abort, current_app,
    make_response, Response
)


class InMemoryRateLimiter:
    """
    Thread-safe in-memory sliding-window rate limiter.
    Tracks request timestamps per IP address / client identifier.
    Zero external dependencies (no Redis required for single-node / dev environments).
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._records = {}  # key: [(timestamp, ...)]

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check if request is permitted under rate limit policy.
        Returns: (allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._records.get(key, [])
            # Filter timestamps outside the sliding window
            valid_timestamps = [ts for ts in timestamps if ts > cutoff]

            if len(valid_timestamps) >= max_requests:
                # Rate limit exceeded
                earliest = valid_timestamps[0]
                retry_after = max(1, int(window_seconds - (now - earliest)))
                self._records[key] = valid_timestamps
                return False, retry_after

            # Append current timestamp
            valid_timestamps.append(now)
            self._records[key] = valid_timestamps
            return True, 0

    def reset(self):
        """Reset all rate limiter records (useful for testing)."""
        with self._lock:
            self._records.clear()


# Global rate limiter instance
limiter = InMemoryRateLimiter()


def rate_limit(max_requests: int = 10, window_seconds: int = 60, error_message: Optional[str] = None):
    """
    Decorator to apply sliding-window rate limiting to Flask route functions.
    Identifies clients by remote IP address.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if rate limiting is enabled
            if current_app.config.get('TESTING') and not current_app.config.get('ENABLE_RATE_LIMIT_TEST'):
                return f(*args, **kwargs)

            # Determine client IP (handles standard X-Forwarded-For if behind reverse proxy)
            forwarded = request.headers.get('X-Forwarded-For')
            if forwarded:
                client_ip = forwarded.split(',')[0].strip()
            else:
                client_ip = request.remote_addr or '127.0.0.1'

            endpoint_key = f"{request.endpoint}:{client_ip}"
            allowed, retry_after = limiter.is_allowed(endpoint_key, max_requests, window_seconds)

            if not allowed:
                msg = error_message or f"Too many requests. Please wait {retry_after} seconds before trying again."
                if request.is_json or request.path.startswith('/api/'):
                    response = jsonify({
                        'error': 'Too Many Requests',
                        'message': msg,
                        'retry_after': retry_after
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(retry_after)
                    return response

                response = make_response(render_template(
                    'errors/429.html',
                    message=msg,
                    retry_after=retry_after
                ), 429)
                response.headers['Retry-After'] = str(retry_after)
                return response

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def init_security(app):
    """
    Initialize Phase 8 security configurations and response filters on the Flask application.
    """
    # 1. Cookie & Session Security Settings
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

    # Secure cookies only enabled over HTTPS in production
    is_prod = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('SESSION_COOKIE_SECURE', '').lower() == 'true'
    app.config['SESSION_COOKIE_SECURE'] = is_prod
    app.config['REMEMBER_COOKIE_SECURE'] = is_prod

    # 2. HTTP Security Headers Filter
    @app.after_request
    def set_security_headers(response: Response):
        # Prevent Clickjacking by restricting framing to same origin
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Control referrer information leak
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Restrict browser APIs and hardware permissions
        response.headers['Permissions-Policy'] = (
            "geolocation=(), camera=(), microphone=(), payment=(self)"
        )

        # Enforce HTTPS HSTS when running securely
        if is_prod or request.is_secure:
            response.headers['Strict-Transport-Security'] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content-Security-Policy (Permits trusted CDNs for Bootstrap, Chart.js, Lucide, Google Fonts, and Razorpay)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://checkout.razorpay.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
            "font-src 'self' https://fonts.gstatic.com data:",
            "img-src 'self' data: https://images.pexels.com https://api.qrserver.com",
            "connect-src 'self' https://api.razorpay.com https://lumberjack.razorpay.com",
            "frame-src 'self' https://api.razorpay.com https://checkout.razorpay.com",
            "frame-ancestors 'self'",
            "base-uri 'self'",
            "form-action 'self' https://api.razorpay.com"
        ]
        response.headers['Content-Security-Policy'] = "; ".join(csp_directives)

        return response
