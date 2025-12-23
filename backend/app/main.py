from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.routes import auth_router, memes_router, trading_router
from app.services.meme_service import seed_sample_memes, migrate_legacy_memes

# Create FastAPI app
app = FastAPI(
    title="MemeStreet API",
    description="The Wall Street of Internet Culture - Trade memes like stocks!",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
)

# CORS middleware - allow frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event - connect to MongoDB
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    # Seed sample memes on startup
    await seed_sample_memes()
    # Migrate legacy memes to use orderbook system
    await migrate_legacy_memes()


# Shutdown event - close MongoDB connection
@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Welcome to MemeStreet API! 🚀",
        "docs": "/docs",
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(memes_router, prefix="/api")
app.include_router(trading_router, prefix="/api")


# For debugging - show all routes
if settings.DEBUG:
    @app.get("/routes", tags=["Debug"])
    async def list_routes():
        routes = []
        for route in app.routes:
            if hasattr(route, "methods"):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": route.name
                })
        return routes
