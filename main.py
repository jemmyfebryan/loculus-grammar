from __future__ import annotations

import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Grammar Check", description="Simple grammar checker using AI")

# Setup Jinja2
env = Environment(loader=FileSystemLoader("templates"))

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

client = genai.Client(api_key=api_key)


class GrammarCheckRequest(BaseModel):
    text: Annotated[str, Field(min_length=1, description="Text to check grammar for")]


class GrammarCheckResponse(BaseModel):
    original: str
    corrected: str


def get_grammar_correction(text: str) -> str:
    """Get grammar correction using Gemini AI."""
    prompt = f"""Fix the grammar and spelling of the following text.
Only output the corrected text, no explanations or additional commentary.

Original text: {text}

Corrected text:"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    template = env.get_template("index.html")
    return template.render()


@app.post("/api/check")
async def api_check_grammar(request: GrammarCheckRequest):
    """Check and correct grammar via API."""
    corrected = get_grammar_correction(request.text)
    return {"original": request.text, "corrected": corrected}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
