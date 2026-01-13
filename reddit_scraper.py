"""
Reddit Scraper - Reddit'ten popüler postları çeker
Gelişmiş HTTP headers ile .json endpoint kullanır
"""
import json
import hashlib
import requests
import random
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger

from config import config, CACHE_DIR


# Gerçekçi User-Agent listesi
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


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
    """Reddit .json API kullanarak post toplayan scraper"""
    
    BASE_URL = "https://old.reddit.com"  # old.reddit.com daha az agresif engelleme yapıyor
    
    def __init__(self):
        self.session = requests.Session()
        self._update_headers()
        self.cache_file = CACHE_DIR / "reddit_cache.json"
        self.posted_file = CACHE_DIR / "posted_ids.json"
        self.request_count = 0
    
    def _update_headers(self):
        """Gerçekçi browser headers ayarla"""
        user_agent = random.choice(USER_AGENTS)
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        })
    
    def _rate_limit(self):
        """Rate limiting - Reddit'i spam'lemekten kaçın"""
        self.request_count += 1
        if self.request_count > 1:
            # Her istek arasında 2-5 saniye bekle
            delay = random.uniform(2, 5)
            logger.debug(f"Rate limiting: waiting {delay:.1f}s")
            time.sleep(delay)
        
        # Her 10 istekte bir headers'ı yenile
        if self.request_count % 10 == 0:
            self._update_headers()
    
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
        
        # Rate limiting uygula
        self._rate_limit()
        
        # Reddit'ten çek - old.reddit.com kullan
        url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
        params = {"limit": limit, "raw_json": 1}
        
        try:
            logger.info(f"Fetching r/{subreddit}/{sort}...")
            response = self.session.get(url, params=params, timeout=15)
            
            # 403 veya 429 durumunda bekle ve tekrar dene
            if response.status_code in [403, 429]:
                logger.warning(f"Got {response.status_code} for r/{subreddit}, waiting and retrying...")
                time.sleep(random.uniform(10, 20))
                self._update_headers()
                response = self.session.get(url, params=params, timeout=15)
            
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})
                
                # Filtrele: minimum upvote
                if post_data.get("score", 0) < config.reddit.min_upvotes:
                    continue
                
                # Stickied postları atla
                if post_data.get("stickied", False):
                    continue
                
                post = RedditPost(
                    id=post_data.get("id", ""),
                    title=post_data.get("title", ""),
                    subreddit=post_data.get("subreddit", subreddit),
                    score=post_data.get("score", 0),
                    num_comments=post_data.get("num_comments", 0),
                    url=post_data.get("url", ""),
                    selftext=post_data.get("selftext", ""),
                    created_utc=post_data.get("created_utc", 0),
                    permalink=post_data.get("permalink", "")
                )
                posts.append(post)
            
            # Cache'e kaydet
            cache[cache_key] = [p.to_dict() for p in posts]
            cache[f"{cache_key}_time"] = datetime.now().isoformat()
            self._save_cache(cache)
            
            logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
            return posts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching r/{subreddit}: {e}")
            return []
    
    def fetch_all_subreddits(self, sort: str = "hot") -> List[RedditPost]:
        """Tüm subredditlerden postları çek ve birleştir"""
        all_posts = []
        posted_ids = self._load_posted_ids()
        successful_fetches = 0
        
        for subreddit in config.reddit.subreddits:
            posts = self.fetch_subreddit(subreddit, sort)
            
            if posts:
                successful_fetches += 1
            
            # Daha önce paylaşılmamış olanları filtrele
            new_posts = [p for p in posts if p.id not in posted_ids]
            all_posts.extend(new_posts)
        
        # Engagement score'a göre sırala
        all_posts.sort(key=lambda p: p.engagement_score, reverse=True)
        
        logger.info(f"Total new posts collected: {len(all_posts)} from {successful_fetches} subreddits")
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
    posts = scraper.fetch_subreddit("programming", limit=5)
    print(f"\n=== r/programming Top Posts ===")
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
