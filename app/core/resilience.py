"""Shared downstream resilience policy helpers."""

import os
from typing import Any, Dict

import httpx
from pyresilience import BulkheadConfig, CircuitBreakerConfig, RetryConfig


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    return int(raw_value)


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    return float(raw_value)


def downstream_error_detail(response: httpx.Response) -> str:
    detail = response.text.strip()
    if detail:
        return detail
    return response.reason_phrase or "Downstream request failed"


def build_http_resilience_policy(service_name: str) -> Dict[str, Any]:
    prefix = f"{service_name.upper().replace('-', '_')}_RESILIENCE"

    return {
        "retry": RetryConfig(
            max_attempts=_env_int(f"{prefix}_RETRY_MAX_ATTEMPTS", 3),
            delay=_env_float(f"{prefix}_RETRY_DELAY_SECONDS", 0.5),
            backoff_factor=_env_float(f"{prefix}_RETRY_BACKOFF_FACTOR", 2.0),
            max_delay=_env_float(f"{prefix}_RETRY_MAX_DELAY_SECONDS", 30.0),
            jitter=True,
            retry_on=(httpx.RequestError,),
        ),
        "circuit_breaker": CircuitBreakerConfig(
            failure_threshold=_env_int(f"{prefix}_CIRCUIT_FAILURE_THRESHOLD", 5),
            recovery_timeout=_env_float(f"{prefix}_CIRCUIT_RECOVERY_TIMEOUT_SECONDS", 30.0),
            success_threshold=_env_int(f"{prefix}_CIRCUIT_SUCCESS_THRESHOLD", 2),
            error_types=(httpx.RequestError, httpx.HTTPStatusError),
        ),
        "bulkhead": BulkheadConfig(
                max_concurrent=_env_int(f"{prefix}_BULKHEAD_MAX_CONCURRENT", 20),
            max_wait=_env_float(f"{prefix}_BULKHEAD_MAX_WAIT_SECONDS", 0.0),
        ),
    }


def build_admin_http_resilience_policy(service_name: str) -> Dict[str, Any]:
    prefix = f"{service_name.upper().replace('-', '_')}_ADMIN_RESILIENCE"

    return {
        "retry": RetryConfig(
            max_attempts=_env_int(f"{prefix}_RETRY_MAX_ATTEMPTS", 3),
            delay=_env_float(f"{prefix}_RETRY_DELAY_SECONDS", 0.5),
            backoff_factor=_env_float(f"{prefix}_RETRY_BACKOFF_FACTOR", 2.0),
            max_delay=_env_float(f"{prefix}_RETRY_MAX_DELAY_SECONDS", 30.0),
            jitter=True,
            retry_on=(httpx.RequestError,),
        ),
        "circuit_breaker": CircuitBreakerConfig(
            failure_threshold=_env_int(f"{prefix}_CIRCUIT_FAILURE_THRESHOLD", 5),
            recovery_timeout=_env_float(f"{prefix}_CIRCUIT_RECOVERY_TIMEOUT_SECONDS", 30.0),
            success_threshold=_env_int(f"{prefix}_CIRCUIT_SUCCESS_THRESHOLD", 2),
            error_types=(httpx.RequestError, httpx.HTTPStatusError),
        ),
        "bulkhead": BulkheadConfig(
            max_concurrent=_env_int(f"{prefix}_BULKHEAD_MAX_CONCURRENT", 5),
            max_wait=_env_float(f"{prefix}_BULKHEAD_MAX_WAIT_SECONDS", 0.0),
        ),
    }