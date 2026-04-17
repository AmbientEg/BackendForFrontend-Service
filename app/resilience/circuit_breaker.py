import time
import asyncio
from functools import wraps

class AsyncCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()

            if self.state == "OPEN":
                if now - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit is OPEN")

            try:
                result = await func(*args, **kwargs)

                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failures = 0

                return result

            except Exception as e:
                self.failures += 1
                self.last_failure_time = now

                if self.failures >= self.failure_threshold:
                    self.state = "OPEN"

                raise e

        return wrapper