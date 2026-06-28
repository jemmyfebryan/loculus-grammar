"""Library management routes."""
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import LibraryCreateRequest, LibraryUpdateRequest, TextCreateRequest, TextUpdateRequest
from app.services import library as library_service

router = APIRouter()


def get_templates() -> Jinja2Templates:
    """Get Jinja2 templates instance."""
    from app.main import templates
    return templates


@router.get("/library", response_class=HTMLResponse, name="library_page")
async def library_page(request: Request):
    """Render the library management page."""
    if not request.session.get("authenticated"):
        return RedirectResponse(url=request.app.url_path_for("login_page"), status_code=303)
    username = request.session.get("username", "User")
    templates = get_templates()
    return templates.TemplateResponse(request, "library.html", {
        "request": request,
        "username": username,
        "authenticated": True,
        "page": "library"
    })


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


@router.get("/api/libraries/{library_id}/export")
async def export_library(request: Request, library_id: str):
    """Export a library as a JSON file."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = request.session.get("user_id")
    export_data = library_service.export_library(user_id, library_id)

    if not export_data:
        raise HTTPException(status_code=404, detail="Library not found")

    from fastapi.responses import Response

    json_str = json.dumps(export_data, indent=2)
    filename = f"library_{export_data['library']['name'].replace(' ', '_')}.json"

    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/api/libraries/import")
async def import_library(request: Request):
    """Import a library from a JSON file."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    from fastapi import UploadFile

    user_id = request.session.get("user_id")

    # Parse form data
    form = await request.form()
    file = form.get("file")
    merge_strategy = form.get("merge_strategy", "merge")
    target_library_id = form.get("target_library_id")

    # More lenient file check - check if it has a filename
    if not file or not hasattr(file, 'filename') or not file.filename:
        raise HTTPException(status_code=400, detail="File is required")

    if merge_strategy not in ["replace", "merge"]:
        raise HTTPException(status_code=400, detail="Invalid merge_strategy")

    try:
        contents = await file.read()
        import_data = json.loads(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    library = library_service.import_library(
        user_id,
        import_data,
        target_library_id=target_library_id,
        merge_strategy=merge_strategy
    )

    if not library:
        raise HTTPException(status_code=400, detail="Failed to import library. Invalid data or target library not found.")

    return {"library": library}
