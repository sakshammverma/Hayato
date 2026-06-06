from langgraph.graph import StateGraph,END
from langgraph.types import Send
import asyncio
from typing import TypedDict, Annotated
import operator
from app.github import get_pr_diff, post_pr_comment
from app.reviewer import review_file
from app.utils import classify_risk

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
    return {"files": files}

def coordinator_node(state: ReviewState):
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
    return sends

async def review_file_node(state: FileReviewState) -> dict:
    review = await review_file(
        pr_title = state["pr_title"],
        pr_description = state["pr_description"],
        repository_name = state["repo_full_name"],
        file_path = state["filename"],
        risk_level = state["risk"],
        diff = state["patch"]
    )
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
    graph.add_node("coordinator",coordinator_node)
    graph.add_node("review_file_node", review_file_node)
    graph.add_node("reducer", reducer_node)

    graph.set_entry_point("fetch_files")
    graph.add_edge("fetch_files", "coordinator")
    graph.add_conditional_edges("coordinator", lambda x: x)
    graph.add_edge("review_file_node", "reducer")
    graph.add_edge("reducer",          END)

    return graph.compile()

review_graph = build_graph()
 