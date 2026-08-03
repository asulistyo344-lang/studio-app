import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes.account import router as account_router
from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.files import router as files_router
from app.api.routes.generation import router as generation_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.projects import router as projects_router
from app.workers.queue import get_arq_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("studio")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq_pool = await get_arq_pool()
    logger.info("[Startup] arq Redis pool connected")
    yield
    await app.state.arq_pool.close()
    logger.info("[Shutdown] arq Redis pool closed")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generation_router)
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(files_router)
app.include_router(notifications_router)
app.include_router(projects_router)
app.include_router(account_router)
app.include_router(admin_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=False)
