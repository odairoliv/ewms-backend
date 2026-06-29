from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.controllers import (
    apontamento_controller,
    audit_controller,
    auth_controller,
    consultor_controller,
    custom_field_controller,
    dashboard_controller,
    empresa_controller,
    fornecedor_controller,
    upload_controller,
    usuario_controller,
)
from app.core.config import settings
from app.core.rate_limit import limiter

app = FastAPI(title="EWMS API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_controller.router, prefix="/api")
app.include_router(usuario_controller.router, prefix="/api")
app.include_router(fornecedor_controller.router, prefix="/api")
app.include_router(consultor_controller.router, prefix="/api")
app.include_router(apontamento_controller.router, prefix="/api")
app.include_router(upload_controller.router, prefix="/api")
app.include_router(audit_controller.router, prefix="/api")
app.include_router(dashboard_controller.router, prefix="/api")
app.include_router(empresa_controller.router, prefix="/api")
app.include_router(custom_field_controller.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
