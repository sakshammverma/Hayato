import asyncio
from app.task_queue import dequeue_jb
from app.github import get_pr_diff, post_pr_comment
from app.reviewer import review_file 
from app.utils import classify_risk
from app.graph import review_graph
from app.database import save_review

async def process_job(job: dict):
    result=await review_graph.ainvoke({
        "pr_number": job["pr_number"],
        "repo_full_name": job["repo_full_name"],
        "pr_title": job["pr_title"],
        "pr_description": job["pr_description"],
        "files": [],
        "reviews": []
    })
    # extract values from graph result
    files_count= len(result.get("files", []))
    reviews_text= "\n".join(result.get("reviews", []))
    
    # count issues by scanning review text
    issues_found = reviews_text.count("* Severity:")
    
    # extract verdict
    if "APPROVE" in reviews_text:
        verdict = "APPROVE"
    elif "REQUEST CHANGES" in reviews_text:
        verdict = "REQUEST CHANGES"
    else:
        verdict = "NEEDS DISCUSSION"

    save_review(
        repo_name=job["repo_full_name"],
        pr_number=job["pr_number"],
        verdict=verdict,
        issues_found=issues_found,
        files_count=files_count
    )
    print(f"[DB] Saved review for PR #{job['pr_number']} | {verdict} | {issues_found} issues")

async def run_worker():
    print("[WORKER] Started, watching queue...")
    while True:
        try:
            job = await asyncio.to_thread(dequeue_jb)
            if job:
                print(f"[WORKER] Processing PR #{job['pr_number']}")
                await process_job(job)
            else:
                await asyncio.sleep(2)   
        except Exception as e:
            print(f"[WORKER] Error: {e}, retrying in 5 sec...")
            await asyncio.sleep(5)