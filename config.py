"""
Configuration management for Reddit X Automation
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

class XConfig(BaseModel):
    """X (Twitter) API configuration"""
    api_key: str = os.getenv("X_API_KEY", "")
    api_secret: str = os.getenv("X_API_SECRET", "")
    access_token: str = os.getenv("X_ACCESS_TOKEN", "")
    access_token_secret: str = os.getenv("X_ACCESS_TOKEN_SECRET", "")
    bearer_token: str = os.getenv("X_BEARER_TOKEN", "")

class OpenAIConfig(BaseModel):
    """OpenAI API configuration"""
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class RedditConfig(BaseModel):
    """Reddit scraping configuration"""
    # Reddit API credentials (for PRAW)
    client_id: str = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent: str = os.getenv("REDDIT_USER_AGENT", "RedditXBot/1.0 by u/YourUsername")
    
    posts_limit: int = int(os.getenv("REDDIT_POSTS_LIMIT", "25"))
    min_upvotes: int = int(os.getenv("MIN_UPVOTES", "100"))
    cache_hours: int = int(os.getenv("CACHE_HOURS", "6"))
    
    # Takip edilecek subredditler
    subreddits: List[str] = [
        # Girişimcilik & SaaS
        "Entrepreneur",
        "startups",
        "SaaS",
        "SideProject",
        "indiehackers",
        "MicroSaas",
        "Business_Ideas",
        "smallbusiness",
        
        # Teknoloji & AI
        "programming",
        "webdev",
        "ChatGPT",
        "vibecoding",
        "artificial",
        
        # Verimlilik
        "productivity",
        "InternetIsBeautiful",
    ]

class TweetConfig(BaseModel):
    """Tweet generation configuration"""
    max_daily_tweets: int = int(os.getenv("MAX_DAILY_TWEETS", "8"))
    min_interval_minutes: int = int(os.getenv("MIN_TWEET_INTERVAL", "60"))
    
    # Hashtag'ler
    hashtags_tr: List[str] = [
        "#girişimcilik", "#startup", "#teknoloji", "#yapayZeka",
        "#saas", "#kodlama", "#yazılım", "#iş"
    ]
    hashtags_en: List[str] = [
        "#startup", "#tech", "#AI", "#SaaS",
        "#coding", "#indiehacker", "#buildinpublic", "#entrepreneur"
    ]

class ScheduleConfig(BaseModel):
    """Scheduling configuration"""
    timezone: str = os.getenv("TIMEZONE", "Europe/Istanbul")
    
    # Paylaşım saatleri (UTC)
    schedule_tr: List[str] = ["06:00", "10:00"]  # 09:00, 13:00 TR
    schedule_en: List[str] = ["14:00", "18:00"]  # 17:00, 21:00 TR (US audience)

class Config(BaseModel):
    """Main configuration"""
    x: XConfig = XConfig()
    openai: OpenAIConfig = OpenAIConfig()
    reddit: RedditConfig = RedditConfig()
    tweet: TweetConfig = TweetConfig()
    schedule: ScheduleConfig = ScheduleConfig()
    
    dry_run: bool = os.getenv("DRY_RUN", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "tr")

# Global config instance
config = Config()

# Paths
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"
DATA_DIR = BASE_DIR / "data"

# Create directories
LOGS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
