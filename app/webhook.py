from fastapi import APIRouter, HTTPException, Request, Depends
from app.security import verify_signature
import asyncio
from app.github import get_pr_diff, post_pr_comment
router = APIRouter()

@router.post("/webhook", dependencies=[Depends(verify_signature)])
async def receive_webhook(request: Request):
    payload = await request.json()

    event_type = request.headers.get("X-GitHub-Event", "unknown")

    if event_type == "ping":
        return {"message": "pong"}
    
    if event_type != "pull_request":
        return {"message": "event ignored"}
    
    action = payload.get("action") 

    if action not in ["opened", "synchronize"]:
        return {"message": f"action '{action}' ignored"}
    
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    pr_number = pr.get("number")
    repo_full_name = repo.get("full_name")

    files = await asyncio.to_thread(get_pr_diff,repo_full_name, pr_number)

    print(f"[WEBHOOK] PR #{pr.get('number')} - {action} - {repo.get('full_name')}")
    for f in files:
        print(f"{f['status']} → {f['filename']}")

    await asyncio.to_thread(post_pr_comment, repo_full_name, pr_number, "reviewing pr..")
    return {"message": "review queued", "pr": pr.get("number")}