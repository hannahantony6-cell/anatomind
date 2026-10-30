from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, learning, progress, quizzes, remediation, topics
from .config import get_settings
from .core.errors import register_error_handlers
from .database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="Anatomind API", version="1.0.0", lifespan=lifespan,
                  description="Privacy-first, local-LLM learning platform for first-year MBBS students. "
                              "Educational use only; not a clinical tool.")
    app.add_middleware(CORSMiddleware, allow_origins=s.cors_origin_list, allow_credentials=True,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization"])
    register_error_handlers(app)
    api = APIRouter(prefix="/api")
    for r in (auth, topics, learning, quizzes, progress, remediation):
        api.include_router(r.router)

    @api.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    app.include_router(api)
    return app


app = create_app()
