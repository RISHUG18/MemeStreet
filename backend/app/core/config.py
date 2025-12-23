from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "memestreet"
    
    # JWT
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # App
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:3000"

    # Trading / IPO (primary offering)
    IPO_PERCENT: float = 0.20  # 20% of total shares sold by the system at IPO price
    IPO_DURATION_MINUTES: int = 60  # fixed initial-price window
    
    # Intrinsic Value Formula: BASE + (Upvotes * UPVOTE_WEIGHT) + (Comments * COMMENT_WEIGHT)
    INTRINSIC_BASE_PRICE: float = 10.0  # Base price for intrinsic value
    INTRINSIC_UPVOTE_WEIGHT: float = 0.5  # Each upvote adds this to intrinsic value
    INTRINSIC_COMMENT_WEIGHT: float = 0.3  # Each comment adds this to intrinsic value
    
    # Trading Band for Post-IPO (peer-to-peer)
    # min_price = TRADING_BAND_MIN_MULTIPLIER * Intrinsic Value
    # max_price = Intrinsic Value * (TRADING_BAND_BASE_MAX_MULTIPLIER + (hype_score * TRADING_BAND_HYPE_FACTOR))
    TRADING_BAND_MIN_MULTIPLIER: float = 0.5  # Min listing price = 0.5 * Intrinsic Value (prevents crash)
    TRADING_BAND_BASE_MAX_MULTIPLIER: float = 2.0  # Base max multiplier before hype bonus
    TRADING_BAND_HYPE_FACTOR: float = 0.05  # Each completed trade adds this to max multiplier

    # Secondary-market fees (seller-only)
    MAKER_FEE_BPS: int = 30  # 0.30% fee taken from seller proceeds
    BURN_SHARE_BPS: int = 5000  # 50% of the fee is burned
    CREATOR_FEE_SHARE_BPS: int = 2000  # 20% of remaining fee goes to creator
    TREASURY_DOC_ID: str = "admin"  # db.treasury document id for admin fees
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
