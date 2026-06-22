"""Grammar check routes."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment
from app.config import ROOT_PATH
from app.models import GrammarCheckRequest
from app.services.grammar import get_grammar_correction

router = APIRouter()


def get_templates_env() -> Environment:
    """Get Jinja2 environment (will be set from main app)."""
    from app.main import get_template_env
    return get_template_env()


@router.get("/grammar", response_class=HTMLResponse, name="grammar_page")
async def grammar_page(request: Request):
    """Render the main grammar check app."""
    if not request.session.get("authenticated"):
        return RedirectResponse(url=ROOT_PATH + request.app.url_path_for("login_page"), status_code=303)
    username = request.session.get("username", "User")
    env = get_templates_env()
    template = env.get_template("index.html")
    return template.render(username=username, authenticated=True, page="grammar", ROOT_PATH=ROOT_PATH)


@router.post("/api/check")
async def api_check_grammar(http_request: Request, request: GrammarCheckRequest):
    """Check and correct grammar via API."""
    keep_writing_style = request.keep_writing_style if request.keep_writing_style is not None else False
    preserve_formatting = request.preserve_formatting if request.preserve_formatting is not None else True
    show_explanations = request.show_explanations if request.show_explanations is not None else False
    multiple_outputs = request.multiple_outputs if request.multiple_outputs is not None else 1

    user_id = http_request.session.get("user_id")

    result = get_grammar_correction(
        request.text,
        request.context,
        request.library_id,
        user_id,
        keep_writing_style,
        preserve_formatting,
        request.custom_instructions,
        show_explanations,
        multiple_outputs
    )
    return {"original": request.text, **result}
