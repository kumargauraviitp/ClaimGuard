from typing import Optional
import contextvars
import uuid

correlation_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("correlation_id", default=None)

def get_correlation_id() -> str:
    return correlation_id_ctx.get() or "system"

def set_correlation_id(corr_id: Optional[str] = None) -> str:
    if not corr_id:
        corr_id = str(uuid.uuid4())
    correlation_id_ctx.set(corr_id)
    return corr_id
