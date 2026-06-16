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
    custom_instructions: Optional[str] = Field(None, description="Custom instructions for grammar correction")
    show_explanations: Optional[bool] = Field(False, description="Show explanations for corrections")
    multiple_outputs: Optional[int] = Field(1, ge=1, le=5, description="Number of alternative outputs (1-5)")


class GrammarOutput(BaseModel):
    text: str
    explanation: Optional[str] = None

class GrammarCheckResponse(BaseModel):
    original: str
    corrected: Optional[str] = None
    explanation: Optional[str] = None
    outputs: Optional[list[GrammarOutput]] = None


def get_grammar_correction(text: str, context: Optional[str] = None, keep_writing_style: bool = False, custom_instructions: Optional[str] = None, show_explanations: bool = False, multiple_outputs: int = 1) -> dict:
    """Get grammar correction using Gemini AI."""
    if keep_writing_style:
        style_instruction = "Maintain the original writing style, tone, and voice. Only fix grammar and spelling errors."
    else:
        style_instruction = ""

    if custom_instructions:
        custom_instruction = f"Additional instructions: {custom_instructions}"
    else:
        custom_instruction = ""

    if show_explanations:
        explanation_instruction = "After providing the corrected text, briefly explain the main changes made."
    else:
        explanation_instruction = ""

    if multiple_outputs > 1:
        outputs_instruction = f"Provide {multiple_outputs} different variations of the corrected text. Format each as 'Option N:' followed by the text."
    else:
        outputs_instruction = ""

    if context:
        prompt = f"""Fix the grammar and spelling of the following text.
Use this context to improve the correction: {context}
{style_instruction}
{custom_instruction}
{explanation_instruction}
{outputs_instruction}

Original text: {text}

Corrected text:"""
    else:
        prompt = f"""Fix the grammar and spelling of the following text.
{style_instruction}
{custom_instruction}
{explanation_instruction}
{outputs_instruction}

Original text: {text}

Corrected text:"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    result = response.text.strip()

    # Parse the response based on options
    if multiple_outputs > 1:
        outputs = []
        lines = result.split('\n')
        current_output = []
        current_explanation = None

        for line in lines:
            line = line.strip()
            if line.lower().startswith('option ') or line.lower().startswith('option'):
                if current_output:
                    text = '\n'.join(current_output).strip()
                    outputs.append(GrammarOutput(text=text, explanation=current_explanation))
                current_output = []
                current_explanation = None
                # Extract explanation if present in same line
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1 and parts[1].strip():
                        current_explanation = parts[1].strip()
            else:
                current_output.append(line)

        if current_output:
            text = '\n'.join(current_output).strip()
            outputs.append(GrammarOutput(text=text, explanation=current_explanation))

        return {"outputs": outputs}
    elif show_explanations:
        # Split explanation and corrected text
        if '\n\n' in result:
            parts = result.split('\n\n', 1)
            explanation = parts[0].strip()
            corrected = parts[1].strip() if len(parts) > 1 else parts[0].strip()
        else:
            lines = result.split('\n', 1)
            explanation = lines[0].strip() if len(lines) > 1 else None
            corrected = lines[1].strip() if len(lines) > 1 else result

        return {"corrected": corrected, "explanation": explanation}
    else:
        return {"corrected": result}


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
    show_explanations = request.show_explanations if request.show_explanations is not None else False
    multiple_outputs = request.multiple_outputs if request.multiple_outputs is not None else 1

    result = get_grammar_correction(
        request.text,
        request.context,
        keep_writing_style,
        request.custom_instructions,
        show_explanations,
        multiple_outputs
    )
    return {"original": request.text, **result}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
