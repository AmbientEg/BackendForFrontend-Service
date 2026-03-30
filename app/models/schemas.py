from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    status: str = "error"
    code: str
    message: str


class SuccessResponse(BaseModel):
    status: str = "success"
    data: Any
