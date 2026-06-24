"""Profile routes."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()


def get_templates() -> Jinja2Templates:
    """Get Jinja2 templates instance."""
    from app.main import templates
    return templates


@router.get("/profile", response_class=HTMLResponse, name="profile_page")
async def profile_page(request: Request):
    """Render the profile page."""
    if not request.session.get("authenticated"):
        return RedirectResponse(url=request.app.url_path_for("login_page"), status_code=303)
    username = request.session.get("username", "User")
    templates = get_templates()
    return templates.TemplateResponse(request, "profile.html", {
        "request": request,
        "username": username,
        "authenticated": True,
        "page": "profile"
    })
