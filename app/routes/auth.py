"""Authentication routes."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.database import load_credentials, save_credentials
from app.models import GridAuthRequest, ChangePasswordRequest

router = APIRouter()

def get_templates() -> Jinja2Templates:
    """Get Jinja2 templates instance."""
    from app.main import templates
    return templates


@router.get("/", name="index")
async def index(request: Request):
    """Redirect to login or grammar page based on auth status."""
    if request.session.get("authenticated"):
        return RedirectResponse(url=request.app.url_path_for("grammar_page"), status_code=303)
    return RedirectResponse(url=request.app.url_path_for("login_page"), status_code=303)


@router.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    """Render the login page."""
    if request.session.get("authenticated"):
        return RedirectResponse(url=request.app.url_path_for("grammar_page"), status_code=303)
    templates = get_templates()
    return templates.TemplateResponse(request, "login.html", {"request": request})


@router.post("/grid-login", name="grid_login")
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
            request.session["user_id"] = user.get("id", "user")
            request.session["username"] = user.get("name", user.get("id", "User"))

            return JSONResponse({
                "success": True,
                "redirect_url": str(request.app.url_path_for("grammar_page"))
            })

    # No pattern matched
    return JSONResponse(
        content={"success": False, "error": "Invalid pattern"},
        status_code=401
    )


@router.post("/change-password", name="change_password")
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


@router.get("/logout", name="logout")
async def logout(request: Request):
    """Handle logout."""
    request.session.clear()
    return RedirectResponse(url=request.app.url_path_for("index"), status_code=303)
