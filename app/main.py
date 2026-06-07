import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.webhook import router
from app.worker import run_worker
from fastapi.responses import JSONResponse
from app.database import init_db
from app.database import get_all_reviews

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(run_worker())
    yield

app = FastAPI(lifespan=lifespan)   
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router)

@app.get("/")
async def dashboard():
    return FileResponse("app/static/index.html")

from app.database import get_all_reviews

@app.get("/api/reviews")
async def reviews_api():
    reviews = await asyncio.to_thread(get_all_reviews)
    return [
        {
            "id":r.id,
            "repo_name":r.repo_name,
            "pr_number": r.pr_number,
            "verdict":r.verdict,
            "issues_found": r.issues_found,
            "files_count":r.files_count,
            "reviewed_at":r.reviewed_at.isoformat()
        }
        for r in reviews
    ]

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return JSONResponse({"status": "ok"})