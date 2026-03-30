from dataclasses import dataclass

from fastapi import status


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int = status.HTTP_400_BAD_REQUEST


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(code="NOT_FOUND", message=message, status_code=status.HTTP_404_NOT_FOUND)


class IntegrationError(AppError):
    def __init__(self, message: str = "Downstream service failure") -> None:
        super().__init__(
            code="INTEGRATION_ERROR",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
