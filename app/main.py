# File: iep_chatbot/app/main.py

import os
import sys

# ---------------------------------------------------
# 1) Insert the “vendor” folder so it takes precedence over system packages.
#
#    Since this file lives at:
#        C:\Users\danie\Documents\IEP_Chat\iep_chatbot\app\main.py
#
#    We need to go up two levels to reach:
#        C:\Users\danie\Documents\IEP_Chat\vendor
#
VENDOR_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "vendor")
)
if VENDOR_PATH not in sys.path:
    sys.path.insert(0, VENDOR_PATH)
# ---------------------------------------------------

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_302_FOUND
import uvicorn

from .chat import chat_post  # Handles the POST /chat logic

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# Mount the “static” folder at /static (for CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Tell Jinja2Templates where to find the HTML templates.
# Because Uvicorn’s working directory is iep_chatbot/, this path resolves to:
#    iep_chatbot/app/templates
templates = Jinja2Templates(directory="app/templates")

# ----------------------------
# Dummy user database for login.
# Feel free to replace or extend this with your own usernames/passwords.
USER_DB = {
    "admin@example.com": "password123"
}
# ----------------------------

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    # Validate credentials against USER_DB
    if email in USER_DB and USER_DB[email] == password:
        request.session["user"] = email
        return RedirectResponse(url="/chat", status_code=HTTP_302_FOUND)

    # If invalid, re-render login.html with an error message
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": "Invalid credentials. Please try again."
        }
    )


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")

    # Render the chat interface, passing “user” so the template can greet them
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})


@app.post("/chat", response_class=HTMLResponse)
async def chat_post_route(
    request: Request,
    user_input: str = Form(...)
):
    # Delegate to chat_post (in app/chat.py), which handles:
    #  1) Retrieving vector‐search results from Redis
    #  2) Sending the prompt + context to OpenAI
    #  3) Formatting the reply (bullets + italicized citations)
    #  4) Saving the conversation back into Redis
    return await chat_post(request, user_input)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")


# If you ever run “python main.py” directly, this will start Uvicorn:
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
