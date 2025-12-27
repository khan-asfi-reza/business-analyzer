
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from routes import auth, dashboard, api, pages, admin
from routes.base import templates


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.info(
        f"Starting: {_app}"
    )
    yield


app = FastAPI(
    title="Business Analyzer",
    description="Investment Decision Support System",
    version="1.0.0",
    lifespan=lifespan
)




@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware for authentication
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-here-change-in-production",
    max_age=7*24*60*60  # 7 days
)

app.mount("/assets/css", StaticFiles(directory="assets/css"), name="css")
app.mount("/js", StaticFiles(directory="assets/js"), name="js")
app.mount("/images", StaticFiles(directory="assets/images"), name="images")

app.include_router(pages.router, tags=["Global Pages"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard Pages"])
app.include_router(admin.router, prefix="/admin", tags=["Admin pages Pages"])
app.include_router(api.router, prefix="/api", tags=["API"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Business Analyzer",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)