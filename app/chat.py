from fastapi import Request, Form
from fastapi.responses import JSONResponse, RedirectResponse
from openai import OpenAI
from fastapi.templating import Jinja2Templates
import os
import re
from dotenv import load_dotenv

from .vector_search import query_redis
from .redis_memory import get_chat_history, append_to_chat_history

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
templates = Jinja2Templates(directory="app/templates")


def format_citations(text: str) -> str:
    return re.sub(r"(Cal\. Educ\. Code\s§\s?\d+[a-zA-Z0-9()]*|\§\s?\d+[a-zA-Z0-9()]*)", r"<em>\1</em>", text)


def format_bullet_list(text: str) -> str:
    """
    Converts lines starting with '1.' into a single <ul><li>...</li></ul> block,
    treating them as bullet points instead of numbered items.
    """
    lines = text.split('\n')
    formatted_lines = []
    inside_list = False

    for line in lines:
        stripped = line.strip()

        if re.match(r"^1\.\s", stripped):
            if not inside_list:
                formatted_lines.append("<ul>")
                inside_list = True
            content = stripped.split('.', 1)[1].strip()
            formatted_lines.append(f"<li>{content}</li>")
        else:
            if inside_list:
                formatted_lines.append("</ul>")
                inside_list = False
            if stripped:
                formatted_lines.append(f"<p>{stripped}</p>")

    if inside_list:
        formatted_lines.append("</ul>")

    return '\n'.join(formatted_lines)


async def chat_post(request: Request, user_input: str = Form(...)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Limit context
    context_chunks = query_redis(user_input, top_k=2)
    context_text = "\n\n".join(context_chunks[:2])

    # Limit history
    history = get_chat_history(user)
    if len(history) > 10:
        history = history[-10:]

    messages = history + [
        {
            "role": "system",
            "content": (
                "You are a helpful and supportive healthcare professional with expertise in California special education law. "
                "When answering questions, keep your responses concise and easy to scan using short paragraphs and bullet points. "
                "Avoid long blocks of text or excessive explanation. Only cite relevant California Education Code sections using "
                "the format '§ [section number]' and include those citations in italics at the end if applicable. "
                "If a user's question is ambiguous or missing key details, politely ask clarifying questions before giving your final answer."
            )
        },
        {
            "role": "user",
            "content": f"{user_input}\n\nRefer to the following:\n{context_text}"
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.5,
        max_tokens=700,
        presence_penalty=0.3,
        frequency_penalty=0.5
    )

    bot_reply = response.choices[0].message.content
    formatted = format_bullet_list(bot_reply)
    formatted = format_citations(formatted)

    append_to_chat_history(user, user_input, bot_reply)

    return JSONResponse(content={
        "user_message": user_input,
        "bot_response": formatted
    })
