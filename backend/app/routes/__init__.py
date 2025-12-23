from .auth import router as auth_router
from .memes import router as memes_router
from .trading import router as trading_router

__all__ = ["auth_router", "memes_router", "trading_router"]
