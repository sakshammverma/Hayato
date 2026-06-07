from langgraph.graph import StateGraph,END
from langgraph.types import Send
import asyncio
from typing import TypedDict, Annotated
import operator
from app.github import get_pr_diff, post_pr_comment
from app.reviewer import review_file
from app.utils import classify_risk
from app.cache import get_cached_review, cache_review
from app.sandbox import run_sandbox, SandboxResult

class ReviewState(TypedDict):
    pr_number:int
    repo_full_name: str
    pr_title: str
    pr_description: str
    files: list[dict]
    reviews: Annotated[list[str], operator.add]

class FileReviewState(TypedDict):
    pr_title: str
    pr_description: str
    repo_full_name: str
    filename: str
    patch: str 
    risk: str

async def fetch_files_node(state: ReviewState) -> dict:
    files = await asyncio.to_thread(
        get_pr_diff,
        state["repo_full_name"],
        state["pr_number"]
    )
    print(f"DEBUG: Fetched {len(files)} files")
    return {"files": files}

def coordinator_routing(state: ReviewState) -> list:
    sends = []
    for f in state["files"]:
        patch = f.get("patch", "")
        if not patch:
            continue
        sends.append(Send("review_file_node", {
            "pr_title":state["pr_title"],
            "pr_description": state["pr_description"],
            "repo_full_name": state["repo_full_name"],
            "filename": f["filename"],
            "patch": patch,
            "risk": classify_risk(f["filename"])
        }))
    print(f"DEBUG: Coordinator created {len(sends)} parallel tasks")
    return sends

async def review_file_node(state: FileReviewState) -> dict:
    # check for cache first
    cached = get_cached_review(
        state["repo_full_name"],
        state["filename"],
        state["patch"]
    )
     # hit
    if cached:
        print(f"[CACHE] HIT → {state['filename']}")
        result = f"### `{state['filename']}` ({state['risk']} risk)\n\n{cached}"
        return {"reviews": [result]}
    
    # miss, call llm
    print(f"[CACHE] MISS → {state['filename']}, calling LLM..")
    review = await review_file(
        pr_title = state["pr_title"],
        pr_description = state["pr_description"],
        repository_name = state["repo_full_name"],
        file_path = state["filename"],
        risk_level = state["risk"],
        diff = state["patch"]
    )

    # sandbox check for vuln.
    sandbox_result = await asyncio.to_thread(
        run_sandbox, 
        state["patch"], 
        state["filename"]
    )
    if not sandbox_result.passed:
        review += "\n\n##Sandbox Validation\n"
        if not sandbox_result.syntax_valid:
            review += "Syntax errors detected\n"
        for issue in sandbox_result.flake8_issues:
            review += f"- {issue}\n"
        for issue in sandbox_result.bandit_issues:
            review += f"{issue}\n"
    else:
        review += "\n\n##Sandbox Validation\nNo issues found"

    # store in cache for next time 
    cache_review(state["repo_full_name"], state["filename"], state["patch"], review)
    result = f"### `{state['filename']}` ({state['risk']} risk)\n\n{review}"
    return {"reviews": [result]}

async def reducer_node(state: ReviewState) -> dict:
    if not state["reviews"]:
        return {}
    
    combined = "\n\n---\n\n".join(state["reviews"])
    await asyncio.to_thread(
        post_pr_comment,
        state["repo_full_name"],
        state["pr_number"],
        combined
    )
    
    return {}

def build_graph():
    graph = StateGraph(ReviewState)

    graph.add_node("fetch_files", fetch_files_node) 
    graph.add_node("review_file_node", review_file_node)
    graph.add_node("reducer", reducer_node)

    graph.set_entry_point("fetch_files")
    graph.add_conditional_edges("fetch_files", coordinator_routing)
    graph.add_edge("review_file_node", "reducer")
    graph.add_edge("reducer", END)

    return graph.compile()

review_graph = build_graph()
 