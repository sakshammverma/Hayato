import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise RuntimeError("REDIS_URL environment variable is not set")

client = redis.from_url(
    redis_url,
    decode_responses=True,
    single_connection_client=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

QUEUE_NAME = "pr_review_jobs"

def enqueue_jb(job: dict):
    try:
        client.lpush(QUEUE_NAME, json.dumps(job))
    except Exception as e:
        print(f"[QUEUE] Enqueue error: {e}")

def dequeue_jb():
    try:
        job = client.lpop(QUEUE_NAME)
        if job is None:
            return None
        return json.loads(job)  # type: ignore
    except Exception as e:
        print(f"[QUEUE] Dequeue error: {e}")
        return None