from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class BaseResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[ErrorDetail] = None

def success_response(data: T = None, message: str = None) -> BaseResponse[T]:
    return BaseResponse(success=True, data=data, message=message)

def error_response(code: str, message: str, details: Any = None) -> BaseResponse[Any]:
    return BaseResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, details=details)
    )
