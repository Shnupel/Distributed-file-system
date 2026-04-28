from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middlewares import limiter
from app.api.v1 import router as v1_router
from app.core import API_V1_PREFIX, get_settings
from app.exceptions import register_exception_handlers
from app.lifespan import lifespan


settings = get_settings()

app = FastAPI(
    title="DFS Master Node API",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.state.limiter = limiter
register_exception_handlers(app)
app.include_router(v1_router, prefix=API_V1_PREFIX)