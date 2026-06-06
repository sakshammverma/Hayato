from fastapi import APIRouter, Request, Depends
from app.security import verify_signature
from app.task_queue import enqueue_jb

router = APIRouter()

@router.post("/webhook", dependencies=[Depends(verify_signature)])
async def receive_webhook(request: Request):
    payload = await request.json()

    event_type = request.headers.get("x-github-event", "unknown")

    if event_type == "ping":
        return {"message": "pong"}

    if event_type != "pull_request":
        return {"message": "event ignored"}

    action = payload.get("action")

    if action not in ["opened", "synchronize"]:
        return {"message": f"action '{action}' ignored"}

    pr   = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    pr_number      = pr.get("number")
    repo_full_name = repo.get("full_name")

    job ={
        "pr_number":pr_number,
        "repo_full_name": repo_full_name,
        "pr_title": pr.get("title", ""),
        "pr_description": pr.get("body", "")
    }
    enqueue_jb(job)

    return {"message": "review queued", "pr": pr_number}