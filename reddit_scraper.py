"""
Reddit Scraper - Reddit'ten popüler postları çeker
PRAW (Python Reddit API Wrapper) kullanarak resmi API ile çalışır
"""
import json
import hashlib
import praw
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger

from config import config, CACHE_DIR


@dataclass
class RedditPost:
    """Reddit post data model"""
    id: str
    title: str
    subreddit: str
    score: int
    num_comments: int
    url: str
    selftext: str
    created_utc: float
    permalink: str
    
    @property
    def reddit_url(self) -> str:
        return f"https://reddit.com{self.permalink}"
    
    @property
    def engagement_score(self) -> float:
        """Engagement hesapla (upvote + comment ağırlıklı)"""
        return self.score + (self.num_comments * 2)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "subreddit": self.subreddit,
            "score": self.score,
            "num_comments": self.num_comments,
            "url": self.url,
            "selftext": self.selftext[:500] if self.selftext else "",
            "created_utc": self.created_utc,
            "permalink": self.permalink,
            "reddit_url": self.reddit_url,
            "engagement_score": self.engagement_score
        }


class RedditScraper:
    """Reddit PRAW API kullanarak post toplayan scraper"""
    
    def __init__(self):
        # PRAW Reddit instance oluştur
        self.reddit = praw.Reddit(
            client_id=config.reddit.client_id,
            client_secret=config.reddit.client_secret,
            user_agent=config.reddit.user_agent
        )
        self.cache_file = CACHE_DIR / "reddit_cache.json"
        self.posted_file = CACHE_DIR / "posted_ids.json"
        
        # API credentials kontrolü
        if not config.reddit.client_id or not config.reddit.client_secret:
            logger.warning("Reddit API credentials not set! Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
    
    def _get_cache_key(self, subreddit: str, sort: str) -> str:
        """Cache key oluştur"""
        return hashlib.md5(f"{subreddit}_{sort}".encode()).hexdigest()
    
    def _is_cache_valid(self, cache_time: str) -> bool:
        """Cache geçerli mi kontrol et"""
        try:
            cached_dt = datetime.fromisoformat(cache_time)
            return datetime.now() - cached_dt < timedelta(hours=config.reddit.cache_hours)
        except:
            return False
    
    def _load_cache(self) -> dict:
        """Cache'i yükle"""
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text())
            except:
                return {}
        return {}
    
    def _save_cache(self, cache: dict):
        """Cache'i kaydet"""
        self.cache_file.write_text(json.dumps(cache, indent=2))
    
    def _load_posted_ids(self) -> set:
        """Daha önce paylaşılan post ID'lerini yükle"""
        if self.posted_file.exists():
            try:
                data = json.loads(self.posted_file.read_text())
                return set(data.get("ids", []))
            except:
                return set()
        return set()
    
    def _save_posted_id(self, post_id: str):
        """Paylaşılan post ID'sini kaydet"""
        posted = self._load_posted_ids()
        posted.add(post_id)
        
        # Son 1000 ID'yi tut (eski olanları temizle)
        posted_list = list(posted)[-1000:]
        
        self.posted_file.write_text(json.dumps({
            "ids": posted_list,
            "updated_at": datetime.now().isoformat()
        }, indent=2))
    
    def fetch_subreddit(
        self, 
        subreddit: str, 
        sort: str = "hot",
        limit: int = None
    ) -> List[RedditPost]:
        """
        Subreddit'ten postları çek
        
        Args:
            subreddit: Subreddit adı (r/ olmadan)
            sort: hot, new, top, rising
            limit: Kaç post çekilecek
        """
        limit = limit or config.reddit.posts_limit
        
        # Cache kontrol
        cache = self._load_cache()
        cache_key = self._get_cache_key(subreddit, sort)
        
        if cache_key in cache and self._is_cache_valid(cache.get(f"{cache_key}_time", "")):
            logger.debug(f"Cache hit for r/{subreddit}")
            return [RedditPost(**p) for p in cache[cache_key]]
        
        # Reddit'ten PRAW ile çek
        try:
            logger.info(f"Fetching r/{subreddit}/{sort}...")
            sub = self.reddit.subreddit(subreddit)
            
            # Sort tipine göre postları al
            if sort == "hot":
                submissions = sub.hot(limit=limit)
            elif sort == "new":
                submissions = sub.new(limit=limit)
            elif sort == "top":
                submissions = sub.top(limit=limit, time_filter="day")
            elif sort == "rising":
                submissions = sub.rising(limit=limit)
            else:
                submissions = sub.hot(limit=limit)
            
            posts = []
            for submission in submissions:
                # Filtrele: minimum upvote
                if submission.score < config.reddit.min_upvotes:
                    continue
                
                # Stickied postları atla
                if submission.stickied:
                    continue
                
                post = RedditPost(
                    id=submission.id,
                    title=submission.title,
                    subreddit=submission.subreddit.display_name,
                    score=submission.score,
                    num_comments=submission.num_comments,
                    url=submission.url,
                    selftext=submission.selftext or "",
                    created_utc=submission.created_utc,
                    permalink=submission.permalink
                )
                posts.append(post)
            
            # Cache'e kaydet
            cache[cache_key] = [p.to_dict() for p in posts]
            cache[f"{cache_key}_time"] = datetime.now().isoformat()
            self._save_cache(cache)
            
            logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching r/{subreddit}: {e}")
            return []
    
    def fetch_all_subreddits(self, sort: str = "hot") -> List[RedditPost]:
        """Tüm subredditlerden postları çek ve birleştir"""
        all_posts = []
        posted_ids = self._load_posted_ids()
        
        for subreddit in config.reddit.subreddits:
            posts = self.fetch_subreddit(subreddit, sort)
            
            # Daha önce paylaşılmamış olanları filtrele
            new_posts = [p for p in posts if p.id not in posted_ids]
            all_posts.extend(new_posts)
        
        # Engagement score'a göre sırala
        all_posts.sort(key=lambda p: p.engagement_score, reverse=True)
        
        logger.info(f"Total new posts collected: {len(all_posts)}")
        return all_posts
    
    def get_top_post(self) -> Optional[RedditPost]:
        """En popüler paylaşılmamış postu getir"""
        posts = self.fetch_all_subreddits()
        
        if posts:
            top_post = posts[0]
            logger.info(f"Top post: [{top_post.subreddit}] {top_post.title[:50]}... (score: {top_post.score})")
            return top_post
        
        logger.warning("No new posts found")
        return None
    
    def mark_as_posted(self, post_id: str):
        """Postu paylaşıldı olarak işaretle"""
        self._save_posted_id(post_id)
        logger.debug(f"Marked post {post_id} as posted")


# Test için
if __name__ == "__main__":
    from loguru import logger
    import sys
    
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    scraper = RedditScraper()
    
    # Tek subreddit test
    posts = scraper.fetch_subreddit("SaaS", limit=5)
    print(f"\n=== r/SaaS Top Posts ===")
    for post in posts[:3]:
        print(f"[{post.score}] {post.title[:60]}...")
    
    # En popüler post
    print(f"\n=== Top Unposted Post ===")
    top = scraper.get_top_post()
    if top:
        print(f"Subreddit: r/{top.subreddit}")
        print(f"Title: {top.title}")
        print(f"Score: {top.score}")
        print(f"Comments: {top.num_comments}")
        print(f"URL: {top.reddit_url}")
