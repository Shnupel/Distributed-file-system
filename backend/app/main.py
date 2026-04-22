from fastapi import FastAPI

from app.api.middlewares import limiter
from app.api.v1 import router as v1_router
from app.core import API_V1_PREFIX, get_settings
from app.exceptions import register_exception_handlers
from app.lifespan import lifespan


settings = get_settings()

app = FastAPI(
    title="My Auth API",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.state.limiter = limiter
register_exception_handlers(app)
app.include_router(v1_router, prefix=API_V1_PREFIX)