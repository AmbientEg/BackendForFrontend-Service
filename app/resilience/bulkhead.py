import asyncio
from functools import wraps

def bulkhead(limit: int):
    semaphore = asyncio.Semaphore(limit)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with semaphore:
                return await func(*args, **kwargs)
        return wrapper

    return decorator