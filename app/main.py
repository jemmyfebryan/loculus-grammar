"""Main application entry point."""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from jinja2 import Environment, FileSystemLoader

from app.config import SECRET_KEY, ROOT_PATH
from app.routes import auth, grammar, profile, library

# Initialize Jinja2
_template_env = Environment(loader=FileSystemLoader("templates"))

def get_template_env() -> Environment:
    """Get the Jinja2 template environment."""
    return _template_env


# Create FastAPI app
app = FastAPI(
    title="Grammar Check",
    description="Simple grammar checker using AI",
    root_path=ROOT_PATH
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(grammar.router, tags=["grammar"])
app.include_router(library.router, tags=["library"])
app.include_router(profile.router, tags=["profile"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9006)
