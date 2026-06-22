from __future__ import annotations

import json
import os
from typing import Annotated, Optional
from secrets import token_hex

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from google import genai
from google.genai import types
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

SECRET_KEY = token_hex(32)
CREDENTIALS_FILE = "database/grid_credentials.json"

app = FastAPI(title="Grammar Check", description="Simple grammar checker using AI", root_path=os.getenv("FASTAPI_ROOT_PATH", ""))

# Store root_path for use in redirects
ROOT_PATH = os.getenv("FASTAPI_ROOT_PATH", "")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Setup Jinja2
env = Environment(loader=FileSystemLoader("templates"))

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

client = genai.Client(api_key=api_key)


def load_credentials():
    """Load grid credentials from JSON file."""
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('users', [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_credentials(users):
    """Save grid credentials to JSON file."""
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump({"users": users}, f, indent=2)


class Coordinate(BaseModel):
    """Coordinate in the grid."""
    x: int
    y: int


class GridAuthRequest(BaseModel):
    """Grid authentication request."""
    sequence: list[Coordinate] = Field(..., min_length=5, description="Ordered sequence of grid coordinates")


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    action: str = Field(..., description="Action: 'verify_current' or 'change_password'")
    sequence: Optional[list[Coordinate]] = Field(None, description="Current password sequence for verification")
    new_sequence: Optional[list[Coordinate]] = Field(None, description="New password sequence")


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

    if multiple_outputs > 1:
        if show_explanations:
            format_instruction = f"""Provide exactly {multiple_outputs} different corrected versions as a JSON array.
Each element must have:
- "text": the corrected text
- "explanation": brief explanation of changes

Response format:
[
  {{"text": "corrected version 1", "explanation": "explanation 1"}},
  {{"text": "corrected version 2", "explanation": "explanation 2"}}
]
Only output the JSON array, nothing else."""
        else:
            format_instruction = f"""Provide exactly {multiple_outputs} different corrected versions as a JSON array.
Each element must have:
- "text": the corrected text

Response format:
[
  {{"text": "corrected version 1"}},
  {{"text": "corrected version 2"}}
]
Only output the JSON array, nothing else."""
    elif show_explanations:
        format_instruction = """Provide the corrected text as JSON with:
- "text": the corrected text
- "explanation": brief explanation of changes

Response format:
{"text": "corrected text", "explanation": "explanation"}
Only output the JSON object, nothing else."""
    else:
        format_instruction = """Provide only the corrected text as plain JSON.
Response format:
{"text": "corrected text"}
Only output the JSON object, nothing else."""

    if context:
        prompt = f"""Fix the grammar and spelling of the following text.
Use this context to improve the correction: {context}
{style_instruction}
{custom_instruction}

{format_instruction}

Original text: {text}"""
    else:
        prompt = f"""Fix the grammar and spelling of the following text.
{style_instruction}
{custom_instruction}

{format_instruction}

Original text: {text}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    result = response.text.strip()

    # Parse JSON response
    try:
        # Remove markdown code blocks if present
        result = result.strip()
        if result.startswith('```'):
            result = '\n'.join(result.split('\n')[1:-1])
            result = result.strip()
        # Remove json prefix if present
        if result.lower().startswith('json'):
            result = result[4:].strip()

        import json
        data = json.loads(result)

        if multiple_outputs > 1:
            outputs = []
            for item in data:
                if isinstance(item, dict):
                    text = item.get('text', '')
                    explanation = item.get('explanation')
                    outputs.append(GrammarOutput(text=text, explanation=explanation))
            return {"outputs": outputs}
        elif show_explanations:
            return {"corrected": data.get('text', result), "explanation": data.get('explanation')}
        else:
            return {"corrected": data.get('text', result)}
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # Fallback to plain text if JSON parsing fails
        if multiple_outputs > 1 or show_explanations:
            return {"corrected": result, "error": "Failed to parse structured output"}
        else:
            return {"corrected": result}


@app.get("/", name="index")
async def index(request: Request):
    """Redirect to login or grammar page based on auth status."""
    if request.session.get("authenticated"):
        return RedirectResponse(url=f"{ROOT_PATH}/grammar", status_code=303)
    return RedirectResponse(url=ROOT_PATH + request.app.url_path_for("login_page"), status_code=303)


@app.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    """Render the login page."""
    if request.session.get("authenticated"):
        return RedirectResponse(url=ROOT_PATH + request.app.url_path_for("grammar_page"), status_code=303)
    template = env.get_template("login.html")
    return template.render(ROOT_PATH=ROOT_PATH)


@app.post("/grid-login", name="grid_login")
async def grid_login(request: Request, auth_data: GridAuthRequest):
    """Handle grid-based login."""
    users = load_credentials()

    # Check if sequence matches any user's pattern
    for user in users:
        stored_pattern = user.get("pattern", [])

        # Validate sequence length
        if len(auth_data.sequence) != len(stored_pattern):
            continue

        # Check each coordinate in sequence
        is_match = True
        for i, coord in enumerate(auth_data.sequence):
            stored_coord = stored_pattern[i]
            if coord.x != stored_coord["x"] or coord.y != stored_coord["y"]:
                is_match = False
                break

        # If pattern matches, authenticate this user
        if is_match:
            request.session["authenticated"] = True
            request.session["username"] = user.get("name", user.get("id", "User"))

            return JSONResponse({
                "success": True,
                "redirect_url": f"{ROOT_PATH}/grammar"
            })

    # No pattern matched
    return JSONResponse(
        content={"success": False, "error": "Invalid pattern"},
        status_code=401
    )


@app.post("/change-password", name="change_password")
async def change_password(request: Request, req: ChangePasswordRequest):
    """Handle password change."""
    if not request.session.get("authenticated"):
        return JSONResponse(
            content={"success": False, "error": "Not authenticated"},
            status_code=401
        )

    username = request.session.get("username")
    users = load_credentials()

    # Find current user
    user = next((u for u in users if u.get("name") == username), None)
    if not user:
        return JSONResponse(
            content={"success": False, "error": "User not found"},
            status_code=404
        )

    if req.action == "verify_current":
        # Verify current password
        if not req.sequence:
            return JSONResponse(
                content={"valid": False, "error": "No sequence provided"},
                status_code=400
            )

        stored_pattern = user.get("pattern", [])

        if len(req.sequence) != len(stored_pattern):
            return JSONResponse({"valid": False})

        # Check each coordinate
        for i, coord in enumerate(req.sequence):
            stored_coord = stored_pattern[i]
            if coord.x != stored_coord["x"] or coord.y != stored_coord["y"]:
                return JSONResponse({"valid": False})

        return JSONResponse({"valid": True})

    elif req.action == "change_password":
        # Change password
        if not req.new_sequence or len(req.new_sequence) < 5:
            return JSONResponse(
                content={"success": False, "error": "New pattern must be at least 5 cells"},
                status_code=400
            )

        # Update user's pattern
        user["pattern"] = [{"x": coord.x, "y": coord.y} for coord in req.new_sequence]

        # Save to file
        save_credentials(users)

        return JSONResponse({"success": True})

    else:
        return JSONResponse(
            content={"success": False, "error": "Invalid action"},
            status_code=400
        )


@app.get("/grammar", response_class=HTMLResponse, name="grammar_page")
async def grammar_page(request: Request):
    """Render the main grammar check app."""
    if not request.session.get("authenticated"):
        return RedirectResponse(url=ROOT_PATH + request.app.url_path_for("login_page"), status_code=303)
    username = request.session.get("username", "User")
    template = env.get_template("index.html")
    return template.render(username=username, authenticated=True, page="grammar", ROOT_PATH=ROOT_PATH)


@app.get("/profile", response_class=HTMLResponse, name="profile_page")
async def profile_page(request: Request):
    """Render the profile page."""
    if not request.session.get("authenticated"):
        return RedirectResponse(url=ROOT_PATH + request.app.url_path_for("login_page"), status_code=303)
    username = request.session.get("username", "User")
    template = env.get_template("profile.html")
    return template.render(username=username, authenticated=True, page="profile", ROOT_PATH=ROOT_PATH)


@app.get("/logout", name="logout")
async def logout(request: Request):
    """Handle logout."""
    request.session.clear()
    return RedirectResponse(url=ROOT_PATH + request.app.url_path_for("index"), status_code=303)


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

    uvicorn.run(app, host="0.0.0.0", port=9006)
