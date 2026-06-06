import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
if redis_url is None:
    raise EnvironmentError("REDIS_URL is not set")

pool = redis.ConnectionPool.from_url(
    redis_url,
    ssl_cert_reqs=None,
    decode_responses=True,
    max_connections=5
)

client = redis.Redis(connection_pool=pool)

QUEUE_NAME = "pr_review_jobs"

def enqueue_job(job: dict):
    client.lpush(QUEUE_NAME, json.dumps(job))

def dequeue_job():
    try:
        job = client.brpop(QUEUE_NAME, timeout=5)
        if job:
            return json.loads(job[1])
        return None
    except Exception:
        return None