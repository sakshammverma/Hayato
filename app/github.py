import os
from dotenv import load_dotenv
from github import Github
from github.GithubException import GithubException
import asyncio

load_dotenv()

def get_github_client():
    token= os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not set up")
    return Github(token)

def get_pr_diff(repo_full_name: str, pr_number: int) -> list[dict]:
    client= get_github_client()
    repo = client.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    files = pr.get_files()
    
    changed_files=[]
    for file in files:
        changed_files.append({
            "filename": file.filename,
            "status": file.status,
            "additions": file.additions,
            "deletions": file.deletions,
            "patch": file.patch
        })
    return changed_files

def post_pr_comment(repo_full_name: str, pr_number:int, comment:str):
    client = get_github_client()
    repo = client.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(comment)
    