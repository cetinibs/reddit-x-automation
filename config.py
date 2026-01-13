"""
Configuration management for Reddit X Automation
Hurricane Notları stratejilerine göre güncellenmiş versiyon
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
    posts_limit: int = int(os.getenv("REDDIT_POSTS_LIMIT", "25"))
    min_upvotes: int = int(os.getenv("MIN_UPVOTES", "100"))
    cache_hours: int = int(os.getenv("CACHE_HOURS", "6"))
    
    # Takip edilecek subredditler - High-pain niş odaklı
    subreddits: List[str] = [
        # Girişimcilik & SaaS (Yüksek pain point)
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

class EngagementConfig(BaseModel):
    """Hurricane Notları - Engagement stratejisi"""
    # Etkileşim oranları (%90 quote/mention, %10 orijinal post)
    quote_mention_ratio: float = float(os.getenv("QUOTE_MENTION_RATIO", "0.9"))
    original_post_ratio: float = float(os.getenv("ORIGINAL_POST_RATIO", "0.1"))
    
    # 24 saat kuralı - maksimum sessizlik süresi (saat)
    max_silence_hours: int = int(os.getenv("MAX_SILENCE_HOURS", "23"))
    
    # Minimum engagement rate hedefi (%0.5)
    min_engagement_rate: float = float(os.getenv("MIN_ENGAGEMENT_RATE", "0.005"))
    
    # Dwell time hedefi (saniye) - Tartışma yaratma
    target_dwell_time: int = int(os.getenv("TARGET_DWELL_TIME", "5"))
    
    # Büyük hesap takibi için minimum takipçi sayısı
    big_account_min_followers: int = int(os.getenv("BIG_ACCOUNT_MIN_FOLLOWERS", "10000"))
    
    # Günlük quote/mention hedefi
    daily_quote_target: int = int(os.getenv("DAILY_QUOTE_TARGET", "10"))
    daily_mention_target: int = int(os.getenv("DAILY_MENTION_TARGET", "5"))
    
    # Trustscore aktarımı için hedef hesaplar (username listesi)
    target_accounts: List[str] = []

class TweetConfig(BaseModel):
    """Tweet generation configuration"""
    max_daily_tweets: int = int(os.getenv("MAX_DAILY_TWEETS", "8"))
    min_interval_minutes: int = int(os.getenv("MIN_TWEET_INTERVAL", "60"))
    
    # Hurricane: Hashtag kullanma, engagement düşürür
    use_hashtags: bool = os.getenv("USE_HASHTAGS", "false").lower() == "true"
    
    # Hashtag'ler (opsiyonel - varsayılan kapalı)
    hashtags_tr: List[str] = [
        "#girişimcilik", "#startup", "#teknoloji", "#yapayZeka",
        "#saas", "#kodlama", "#yazılım", "#iş"
    ]
    hashtags_en: List[str] = [
        "#startup", "#tech", "#AI", "#SaaS",
        "#coding", "#indiehacker", "#buildinpublic", "#entrepreneur"
    ]
    
    # Duygusal tetikleyiciler (Para, Statü, Beğenilme, Kabul Görme)
    emotional_triggers_tr: List[str] = [
        "para kazanmak", "başarı", "özgürlük", "pasif gelir",
        "statü", "tanınmak", "kabul görmek", "saygı kazanmak"
    ]
    emotional_triggers_en: List[str] = [
        "make money", "success", "freedom", "passive income",
        "status", "recognition", "acceptance", "respect"
    ]

class ScheduleConfig(BaseModel):
    """Scheduling configuration - Hurricane 24 saat kuralı"""
    timezone: str = os.getenv("TIMEZONE", "Europe/Istanbul")
    
    # Paylaşım saatleri (UTC) - 23 saat 59 dk'dan az aralıklarla
    # Hurricane: 24 saatten fazla sessizlik = -%20 negatif boost
    schedule_tr: List[str] = ["06:00", "12:00", "18:00"]  # 3 post/gün = 8 saat aralık
    schedule_en: List[str] = ["09:00", "15:00", "21:00"]  # US audience
    
    # Quote/Mention zamanları (daha sık)
    engagement_schedule: List[str] = [
        "07:00", "09:00", "11:00", "13:00", "15:00", "17:00", "19:00", "21:00"
    ]

class WarmupConfig(BaseModel):
    """Reddit ısınma süreci yapılandırması"""
    # 1 aylık ısınma süresi (gün)
    warmup_days: int = int(os.getenv("WARMUP_DAYS", "30"))
    
    # Isınma modunda mı? (Manuel karma kasma döneminde)
    is_warmup_mode: bool = os.getenv("IS_WARMUP_MODE", "true").lower() == "true"
    
    # Minimum karma gerekliliği otomasyon için
    min_karma_for_automation: int = int(os.getenv("MIN_KARMA", "1000"))
    
    # Günlük karma hedefi
    daily_karma_target: int = int(os.getenv("DAILY_KARMA_TARGET", "50"))

class Config(BaseModel):
    """Main configuration"""
    x: XConfig = XConfig()
    openai: OpenAIConfig = OpenAIConfig()
    reddit: RedditConfig = RedditConfig()
    tweet: TweetConfig = TweetConfig()
    schedule: ScheduleConfig = ScheduleConfig()
    engagement: EngagementConfig = EngagementConfig()
    warmup: WarmupConfig = WarmupConfig()
    
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
