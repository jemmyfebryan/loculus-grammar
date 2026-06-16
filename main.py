from __future__ import annotations

import os
from typing import Annotated, Optional
from secrets import token_hex

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from google import genai
from google.genai import types
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

# Hardcoded credentials
VALID_USERNAME = "alex"
VALID_PASSWORD = "123456"
SECRET_KEY = token_hex(32)

app = FastAPI(title="Grammar Check", description="Simple grammar checker using AI")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Setup Jinja2
env = Environment(loader=FileSystemLoader("templates"))

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

client = genai.Client(api_key=api_key)


class GrammarCheckRequest(BaseModel):
    text: Annotated[str, Field(min_length=1, description="Text to check grammar for")]
    context: Optional[str] = Field(None, description="Additional context to improve grammar correction")
    keep_writing_style: Optional[bool] = Field(False, description="Keep the original writing style")


class GrammarCheckResponse(BaseModel):
    original: str
    corrected: str


def get_grammar_correction(text: str, context: Optional[str] = None, keep_writing_style: bool = False) -> str:
    """Get grammar correction using Gemini AI."""
    if keep_writing_style:
        style_instruction = "Maintain the original writing style, tone, and voice. Only fix grammar and spelling errors."
    else:
        style_instruction = ""

    if context:
        prompt = f"""Fix the grammar and spelling of the following text.
Use this context to improve the correction: {context}
{style_instruction}

Only output the corrected text, no explanations or additional commentary.

Original text: {text}

Corrected text:"""
    else:
        prompt = f"""Fix the grammar and spelling of the following text.
{style_instruction}

Only output the corrected text, no explanations or additional commentary.

Original text: {text}

Corrected text:"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


@app.get("/")
async def index(request: Request):
    """Redirect to login or app based on auth status."""
    if request.session.get("authenticated"):
        return RedirectResponse(url="/app", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    if request.session.get("authenticated"):
        return RedirectResponse(url="/app", status_code=303)
    error = request.session.pop("login_error", None)
    template = env.get_template("login.html")
    return template.render(error=error)


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login."""
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        request.session["authenticated"] = True
        request.session["username"] = username
        return RedirectResponse(url="/app", status_code=303)
    else:
        request.session["login_error"] = "Invalid username or password"
        return RedirectResponse(url="/login", status_code=303)


@app.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    """Render the main grammar check app."""
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=303)
    username = request.session.get("username", "User")
    template = env.get_template("index.html")
    return template.render(username=username)


@app.get("/logout")
async def logout(request: Request):
    """Handle logout."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/check")
async def api_check_grammar(request: GrammarCheckRequest):
    """Check and correct grammar via API."""
    keep_writing_style = request.keep_writing_style if request.keep_writing_style is not None else False
    corrected = get_grammar_correction(request.text, request.context, keep_writing_style)
    return {"original": request.text, "corrected": corrected}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
