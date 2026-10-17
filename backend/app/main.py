from dotenv import find_dotenv, load_dotenv

# .env from the directory the server is started in (backend/)
load_dotenv(find_dotenv(usecwd=True))

import logging  # noqa: E402
import os  # noqa: E402
from contextlib import AsyncExitStack, asynccontextmanager  # noqa: E402

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from app.config.descope import descope_client  # noqa: E402
from app.db.pool import close_pool, get_pool  # noqa: E402
from app.mcp.server import mount_mcp_server  # noqa: E402
from app.routes.agent_routes import router as agent_router  # noqa: E402
from app.routes.connection_routes import router as connection_router  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("agentic-calendar-app")

mcp_server = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with AsyncExitStack() as stack:
        if mcp_server is not None:
            await stack.enter_async_context(mcp_server.session_manager.run())

        logger.info("Agentic Calendar App started")
        yield

        await close_pool()
        await descope_client.aclose()


app = FastAPI(title="Agentic Calendar App", lifespan=lifespan)

cors_origins = ["http://localhost:3000"]
if app_url := os.getenv("APP_URL"):
    for origin in app_url.split(","):
        cleaned = origin.strip().rstrip("/")
        if cleaned and cleaned not in cors_origins:
            cors_origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    # Keep the Node backend's error shape: {"error": "..."}
    return JSONResponse({"error": exc.detail, "success": False}, status_code=exc.status_code)


@app.get("/health")
async def health():
    try:
        pool = await get_pool()
        await pool.fetchval("SELECT 1")
        return {"status": "ok", "service": "agentic-calendar-app", "database": "up"}
    except Exception:
        return JSONResponse(
            {"status": "error", "service": "agentic-calendar-app", "database": "down"},
            status_code=503,
        )


app.include_router(connection_router)
app.include_router(agent_router)

mcp_server = mount_mcp_server(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT") or 4000))
