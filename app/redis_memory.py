import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(
    host=os.getenv("CHAT_REDIS_HOST"),
    port=int(os.getenv("CHAT_REDIS_PORT")),
    password=os.getenv("CHAT_REDIS_PASSWORD"),
    decode_responses=True
)


def get_chat_history(user: str):
    key = f"chat_history:{user}"
    raw = r.get(key)
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"⚠️ Corrupted chat history for user: {user} — clearing.")
        r.delete(key)  # optional: wipe bad data so it doesn't recur
        return []


def append_to_chat_history(user: str, user_input: str, bot_reply: str):
    key = f"chat_history:{user}"
    history = get_chat_history(user)
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": bot_reply})
    r.set(key, json.dumps(history))
