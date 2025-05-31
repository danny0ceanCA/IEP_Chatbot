import os
import redis
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from redis.commands.search.query import Query

load_dotenv()

r = redis.Redis(
    host=os.getenv("VECTOR_REDIS_HOST"),
    port=int(os.getenv("VECTOR_REDIS_PORT")),
    password=os.getenv("VECTOR_REDIS_PASSWORD"),
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
REDIS_INDEX_NAME = "sped_code_index"



def get_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding


def query_redis(query: str, top_k: int = 5):
    query_embedding = get_embedding(query)

    # Convert list to byte array for Redis
    query_vector_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

    q = Query(
        f"*=>[KNN {top_k} @embedding $vec AS score]"
    ).sort_by("score").return_fields("content", "score").dialect(2)

    try:
        res = r.ft(REDIS_INDEX_NAME).search(q, query_params={"vec": query_vector_bytes})
        return [doc.content for doc in res.docs]
    except Exception as e:
        print(f"Redis query error: {e}")
        return []
