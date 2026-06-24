"""Main application entry point."""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import SECRET_KEY, ROOT_PATH
from app.routes import auth, grammar, profile, library


class ForwardedPrefixMiddleware(BaseHTTPMiddleware):
    """Middleware to handle X-Forwarded-Prefix header from proxy."""

    async def dispatch(self, request: Request, call_next):
        # Get the forwarded prefix from proxy
        forwarded_prefix = request.headers.get("X-Forwarded-Prefix", "").rstrip("/")

        if forwarded_prefix:
            # Override the root_path for url generation
            request.scope["root_path"] = forwarded_prefix

        response = await call_next(request)
        return response


# Create FastAPI app
app = FastAPI(
    title="Grammar Check",
    description="Simple grammar checker using AI",
    root_path=ROOT_PATH
)

# Initialize Jinja2Templates with FastAPI
templates = Jinja2Templates(directory="templates")

# Add forwarded prefix middleware BEFORE session middleware
app.add_middleware(ForwardedPrefixMiddleware)

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
