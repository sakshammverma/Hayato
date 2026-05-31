from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

@router.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()

    event_type = request.headers.get("X-GitHub-Event", "unknown")

    if event_type == "ping":
        return {"message": "pong"}
    
    if event_type != "pull_request":
        return {"message": "event ignored"}
    
    action = payload.get("action")
    # We only want to review on "opened" or "synchronize
    if action not in ["opened", "synchronize"]:
        return {"message": f"action '{action}' ignored"}
    
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    print(f"[WEBHOOK] PR #{pr.get('number')} - {action} - {repo.get('full_name')}")

    return {"message": "review queued", "pr": pr.get("number")}