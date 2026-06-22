"""Profile routes."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment
from app.config import ROOT_PATH

router = APIRouter()


def get_templates_env() -> Environment:
    """Get Jinja2 environment (will be set from main app)."""
    from app.main import get_template_env
    return get_template_env()


@router.get("/profile", response_class=HTMLResponse, name="profile_page")
async def profile_page(request: Request):
    """Render the profile page."""
    if not request.session.get("authenticated"):
        return RedirectResponse(url=ROOT_PATH + request.app.url_path_for("login_page"), status_code=303)
    username = request.session.get("username", "User")
    env = get_templates_env()
    template = env.get_template("profile.html")
    return template.render(username=username, authenticated=True, page="profile", ROOT_PATH=ROOT_PATH)
