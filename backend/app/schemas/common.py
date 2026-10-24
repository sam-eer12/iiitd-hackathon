"""Common schema definitions, base models, and pagination helpers."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ErrorDetail(BaseModel):
    code: str
    message: str
    requestId: str
    retryable: bool = False


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
