import asyncio
from app.queue import dequeue_jb
from app.github import get_pr_diff, post_pr_comment
from app.reviewer import review_file
from app.utils import classify_risk

async def process_job(job: dict):
    pr_number      = job["pr_number"]
    repo_full_name = job["repo_full_name"]
    pr_title       = job["pr_title"]
    pr_description = job["pr_description"]

    files = await asyncio.to_thread(get_pr_diff, repo_full_name, pr_number)

    all_reviews = []

    for f in files:
        risk  = classify_risk(f["filename"])
        patch = f.get("patch", "")

        if not patch:
            continue

        review = await review_file(
            pr_title        = pr_title,
            pr_description  = pr_description,
            repository_name = repo_full_name,
            file_path       = f["filename"],
            risk_level      = risk,
            diff            = patch
        )
        all_reviews.append(f"### `{f['filename']}` ({risk} risk)\n\n{review}")

    if all_reviews:
        combined = "\n\n---\n\n".join(all_reviews)
        await asyncio.to_thread(post_pr_comment, repo_full_name, pr_number, combined)

async def run_worker():
    print("[WORKER] Started, watching queue...")
    while True:
        try:
            job = await asyncio.to_thread(dequeue_jb)
            if job:
                print(f"[WORKER] Processing PR #{job['pr_number']}")
                await process_job(job)
        except Exception as e:
            print(f"[WORKER] Error: {e}, retrying in 5 sec...")
            await asyncio.sleep(5)


