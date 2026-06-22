"""Library management routes."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment
from app.config import ROOT_PATH
from app.models import LibraryCreateRequest, LibraryUpdateRequest, TextCreateRequest, TextUpdateRequest
from app.services import library as library_service

router = APIRouter()


def get_templates_env() -> Environment:
    """Get Jinja2 environment (will be set from main app)."""
    from app.main import get_template_env
    return get_template_env()


@router.get("/library", response_class=HTMLResponse, name="library_page")
async def library_page(request: Request):
    """Render the library management page."""
    if not request.session.get("authenticated"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=ROOT_PATH + request.app.url_path_for("login_page"), status_code=303)
    username = request.session.get("username", "User")
    env = get_templates_env()
    template = env.get_template("library.html")
    return template.render(username=username, authenticated=True, page="library", ROOT_PATH=ROOT_PATH)


@router.get("/api/libraries")
async def get_libraries(request: Request):
    """Get all libraries for the current user."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request.session.get("user_id")
    libraries = library_service.get_libraries(user_id)
    return {"libraries": libraries}


@router.post("/api/libraries")
async def create_library(request: Request, lib_data: LibraryCreateRequest):
    """Create a new library."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request.session.get("user_id")
    library = library_service.create_library(user_id, lib_data.name, lib_data.description)
    return {"library": library}


@router.put("/api/libraries/{library_id}")
async def update_library(request: Request, library_id: str, lib_data: LibraryUpdateRequest):
    """Update a library."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request.session.get("user_id")
    library = library_service.update_library(user_id, library_id, lib_data.name, lib_data.description)

    if not library:
        raise HTTPException(status_code=404, detail="Library not found")

    return {"library": library}


@router.delete("/api/libraries/{library_id}")
async def delete_library(request: Request, library_id: str):
    """Delete a library."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request.session.get("user_id")
    success = library_service.delete_library(user_id, library_id)

    if not success:
        raise HTTPException(status_code=404, detail="Library not found")

    return {"success": True}


@router.get("/api/libraries/{library_id}/texts")
async def get_library_texts(request: Request, library_id: str):
    """Get all texts in a library."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request.session.get("user_id")
    texts = library_service.get_texts(user_id, library_id)
    return {"texts": texts}


@router.post("/api/libraries/{library_id}/texts")
async def create_text(request: Request, library_id: str, text_data: TextCreateRequest):
    """Create a new text in a library."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request.session.get("user_id")
    text = library_service.create_text(user_id, library_id, text_data.content)

    if not text:
        raise HTTPException(status_code=404, detail="Library not found")

    return {"text": text}


@router.put("/api/texts/{text_id}")
async def update_text(request: Request, text_id: str, text_data: TextUpdateRequest):
    """Update a text."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request.session.get("user_id")
    text = library_service.update_text(user_id, text_id, text_data.content)

    if not text:
        raise HTTPException(status_code=404, detail="Text not found")

    return {"text": text}


@router.delete("/api/texts/{text_id}")
async def delete_text(request: Request, text_id: str):
    """Delete a text."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request.session.get("user_id")
    success = library_service.delete_text(user_id, text_id)

    if not success:
        raise HTTPException(status_code=404, detail="Text not found")

    return {"success": True}
