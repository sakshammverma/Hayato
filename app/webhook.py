from fastapi import APIRouter, HTTPException, Request, Depends
from app.security import verify_signature
import asyncio
from app.github import get_pr_diff, post_pr_comment
from app.reviewer import review_file

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
    
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    pr_number = pr.get("number")
    repo_full_name = repo.get("full_name")

    files = await asyncio.to_thread(get_pr_diff,repo_full_name, pr_number)

    print(f"[WEBHOOK] PR #{pr.get('number')} - {action} - {repo.get('full_name')}")
    all_reviews=[]
    for f in files:
        risk = classify_risk(f["filename"])
        patch = f.get("patch", "")
        if not patch: 
            continue
        review = await review_file(
        pr_title        = pr.get("title", ""),
        pr_description  = pr.get("body", ""),
        repository_name = repo_full_name,
        file_path       = f["filename"],
        risk_level      = risk,
        diff            = f.get("patch", "")
        )
        all_reviews.append(f"### `{f['filename']}` ({risk} risk)\n\n{review}")

        print(f"{f['status']} → {f['filename']}")

    combined = "\n\n---\n\n".join(all_reviews)
    await asyncio.to_thread(post_pr_comment, repo_full_name, pr_number, combined)
    return {"message": "review queued", "pr": pr.get("number")}


def classify_risk(filename:str) -> str:
    high = ["auth", "crypto", "payment", "admin", "security", "login", "password", "token"]
    low  = ["test_", "_test", "readme", "docs/", ".md"]

    filename_lower = filename.lower()

    if any(ch in filename_lower for ch in high):
        return "high"
    if any(ch in filename_lower for ch in low):
        return "low"
    return "medium"