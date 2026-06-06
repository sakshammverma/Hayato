import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
if redis_url is None:
    raise ValueError("REDIS_URL environment variable is required")

client = redis.from_url(redis_url)

QUEUE_NAME = "pr-review-jbs"

def enqueue_jb(job: dict):
    client.lpush(QUEUE_NAME, json.dumps(job))

def dequeue_job():
    try:
        job = client.brpop(QUEUE_NAME, timeout=5)
        if job:
            return json.loads(job[1])
        return None
    except Exception:
        return None