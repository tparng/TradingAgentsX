"""
Configuration management for TradingAgentsX Backend API
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application settings
    app_name: str = "TradingAgentsX API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False)
    results_dir: str = Field(default="./results")
    
    # API Keys
    openai_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    
    # CORS Configuration
    # Set CORS_ORIGINS environment variable to comma-separated list of allowed origins
    # Example: CORS_ORIGINS=https://your-app.railway.app,https://your-frontend.vercel.app
    cors_origins_str: Optional[str] = Field(default=None, alias="CORS_ORIGINS")
    
    @property
    def cors_origins(self) -> list:
        """Get CORS origins from environment or use defaults"""
        if self.cors_origins_str:
            # Parse comma-separated origins from environment
            origins = [o.strip() for o in self.cors_origins_str.split(",") if o.strip()]
            # Always include localhost for development
            if "http://localhost:3000" not in origins:
                origins.append("http://localhost:3000")
            return origins
        
        # Default origins (fallback - consider removing wildcards in production)
        return [
            "http://localhost:3000",
            "http://frontend:3000",
            "https://*.vercel.app",  # Vercel deployments
            "https://*.onrender.com",  # Render deployments
            "https://*.railway.app",  # Railway deployments
        ]
    
    # TradingAgentsX Configuration
    results_dir: str = "./results"
    max_debate_rounds: int = 1
    max_risk_discuss_rounds: int = 1
    deep_think_llm: str = "claude-sonnet-4-6"
    quick_think_llm: str = "claude-haiku-4-5-20251001"

    # Telegram notifications
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Google Sheets / GCP service account
    google_service_account_json: Optional[str] = None  # JSON string or base64
    google_sheet_id: Optional[str] = None

    # Watchlist auto-analysis scheduler
    watchlist_analysis_cron: Optional[str] = None  # e.g. "0 9 * * 1-5"
    watchlist_deep_think_llm: str = "qwen2.5:14b"
    watchlist_quick_think_llm: str = "qwen2.5:14b"
    watchlist_deep_think_base_url: str = "http://localhost:11434/v1"
    watchlist_quick_think_base_url: str = "http://localhost:11434/v1"
    watchlist_deep_think_api_key: str = "ollama"
    watchlist_quick_think_api_key: str = "ollama"
    watchlist_analysts: str = "market,fundamentals,quant"
    watchlist_report_language: str = "zh-TW"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables like ANTHROPIC_API_KEY, etc.
        populate_by_name = True  # Allow using alias names


# Global settings instance
settings = Settings()
