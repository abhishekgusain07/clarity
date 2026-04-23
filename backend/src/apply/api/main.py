from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apply.api.routes_applications import router as applications_router
from apply.api.routes_health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Apply", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(applications_router)

    return app


app = create_app()
