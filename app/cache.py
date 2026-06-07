import os
from dotenv import load_dotenv
import hashlib
import redis

load_dotenv()

CACHE_TTL = 24*60*60*7  
redis_url= os.getenv("REDIS_URL")
if not redis_url:
    raise RuntimeError("REDIS_URL environment variable is not set")

client= redis.from_url(
    redis_url,
    decode_responses= True,
    single_connection_client=True
)

def get_cache_key(repo: str, filename: str, code_hash: str) -> str:
    return f"review:{repo}:{filename}:{code_hash}"

def hash_patch(patch: str) -> str:
    return hashlib.sha256(patch.encode()).hexdigest()

def get_cached_review(repo: str, filename: str, patch: str):
    key = get_cache_key(repo, filename, hash_patch(patch))
    return client.get(key)
    # returns cached review str or None

def cache_review(repo: str, filename: str, patch: str, review: str):
    key = get_cache_key(repo, filename, hash_patch(patch))
    client.setex(key, CACHE_TTL, review) 
