import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.webhook import router
from app.worker import run_worker
from fastapi.responses import JSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(run_worker())
    yield

app = FastAPI(lifespan=lifespan)   

app.include_router(router)

@app.get("/")
def root():
    return {"status": "running"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return JSONResponse({"status": "ok"})