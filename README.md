# IEP Chatbot

A simple FastAPI application that provides a chat interface powered by the OpenAI API. The chatbot offers concise guidance on California special education law. Conversation history is stored in Redis so that each user's context persists between requests.

To start the application locally:

```bash
uvicorn app.main:app --reload
```

Ensure you have the required environment variables set for the OpenAI and Redis connections.

