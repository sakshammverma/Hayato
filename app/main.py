from fastapi import FastAPI
from app.webhook import router
from contextlib import asynccontextmanager
import asyncio
from app.worker import run_worker

app = FastAPI()

app.include_router(router)

@app.get("/health")
async def health_Check():
    return {"status":"OK"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(run_worker())
    yield


app = FastAPI(lifespan=lifespan)