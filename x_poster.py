"""
X (Twitter) Poster - Tweet paylaşım modülü
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from loguru import logger
import tweepy

from config import config, DATA_DIR


class XPoster:
    """X (Twitter) API kullanarak tweet paylaşan poster"""
    
    def __init__(self):
        self.client = self._create_client()
        self.history_file = DATA_DIR / "tweet_history.json"
    
    def _create_client(self) -> tweepy.Client:
        """Tweepy client oluştur"""
        return tweepy.Client(
            consumer_key=config.x.api_key,
            consumer_secret=config.x.api_secret,
            access_token=config.x.access_token,
            access_token_secret=config.x.access_token_secret,
            bearer_token=config.x.bearer_token
        )
    
    def _load_history(self) -> dict:
        """Tweet geçmişini yükle"""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text())
            except:
                return {"tweets": [], "daily_count": {}}
        return {"tweets": [], "daily_count": {}}
    
    def _save_history(self, history: dict):
        """Tweet geçmişini kaydet"""
        self.history_file.write_text(json.dumps(history, indent=2, ensure_ascii=False))
    
    def _get_daily_count(self) -> int:
        """Bugün kaç tweet atıldığını getir"""
        history = self._load_history()
        today = datetime.now().strftime("%Y-%m-%d")
        return history.get("daily_count", {}).get(today, 0)
    
    def _increment_daily_count(self):
        """Günlük sayacı artır"""
        history = self._load_history()
        today = datetime.now().strftime("%Y-%m-%d")
        
        if "daily_count" not in history:
            history["daily_count"] = {}
        
        history["daily_count"][today] = history["daily_count"].get(today, 0) + 1
        
        # Eski günleri temizle (son 7 gün tut)
        keys_to_remove = []
        for date_key in history["daily_count"]:
            try:
                key_date = datetime.strptime(date_key, "%Y-%m-%d")
                if (datetime.now() - key_date).days > 7:
                    keys_to_remove.append(date_key)
            except:
                pass
        
        for key in keys_to_remove:
            del history["daily_count"][key]
        
        self._save_history(history)
    
    def _log_tweet(self, tweet_id: str, tweet_text: str, language: str, reddit_post_id: str = None):
        """Tweet'i geçmişe kaydet"""
        history = self._load_history()
        
        history["tweets"].append({
            "tweet_id": tweet_id,
            "text": tweet_text,
            "language": language,
            "reddit_post_id": reddit_post_id,
            "posted_at": datetime.now().isoformat()
        })
        
        # Son 500 tweet'i tut
        history["tweets"] = history["tweets"][-500:]
        
        self._save_history(history)
    
    def can_post(self) -> tuple[bool, str]:
        """Tweet atılabilir mi kontrol et"""
        daily_count = self._get_daily_count()
        
        if daily_count >= config.tweet.max_daily_tweets:
            return False, f"Daily limit reached ({daily_count}/{config.tweet.max_daily_tweets})"
        
        return True, "OK"
    
    def post_tweet(
        self, 
        text: str, 
        language: str = "tr",
        reddit_post_id: str = None,
        dry_run: bool = None
    ) -> Optional[str]:
        """
        Tweet paylaş
        
        Args:
            text: Tweet metni
            language: Dil
            reddit_post_id: İlişkili Reddit post ID'si
            dry_run: Kuru çalıştırma (paylaşmadan test)
            
        Returns:
            Tweet ID veya None
        """
        dry_run = dry_run if dry_run is not None else config.dry_run
        
        # Limit kontrolü
        can_post, reason = self.can_post()
        if not can_post:
            logger.warning(f"Cannot post: {reason}")
            return None
        
        # Karakter kontrolü
        if len(text) > 280:
            logger.error(f"Tweet too long: {len(text)} characters")
            return None
        
        if dry_run:
            logger.info(f"[DRY RUN] Would post ({language}): {text[:100]}...")
            return "dry_run_id"
        
        try:
            response = self.client.create_tweet(text=text)
            tweet_id = response.data["id"]
            
            logger.info(f"Posted tweet {tweet_id}")
            
            # Geçmişe kaydet
            self._log_tweet(tweet_id, text, language, reddit_post_id)
            self._increment_daily_count()
            
            return tweet_id
            
        except tweepy.TweepyException as e:
            logger.error(f"Error posting tweet: {e}")
            return None
    
    def post_thread(
        self, 
        tweets: List[str], 
        language: str = "tr",
        dry_run: bool = None
    ) -> List[str]:
        """
        Thread paylaş
        
        Args:
            tweets: Tweet listesi
            language: Dil
            dry_run: Kuru çalıştırma
            
        Returns:
            Tweet ID listesi
        """
        dry_run = dry_run if dry_run is not None else config.dry_run
        
        if not tweets:
            logger.warning("No tweets to post")
            return []
        
        tweet_ids = []
        reply_to_id = None
        
        for i, tweet_text in enumerate(tweets):
            # Karakter kontrolü
            if len(tweet_text) > 280:
                logger.warning(f"Tweet {i+1} too long, truncating...")
                tweet_text = tweet_text[:277] + "..."
            
            if dry_run:
                logger.info(f"[DRY RUN] Thread {i+1}/{len(tweets)}: {tweet_text[:80]}...")
                tweet_ids.append(f"dry_run_{i}")
                continue
            
            try:
                if reply_to_id:
                    response = self.client.create_tweet(
                        text=tweet_text,
                        in_reply_to_tweet_id=reply_to_id
                    )
                else:
                    response = self.client.create_tweet(text=tweet_text)
                
                tweet_id = response.data["id"]
                tweet_ids.append(tweet_id)
                reply_to_id = tweet_id
                
                logger.info(f"Posted thread tweet {i+1}/{len(tweets)}: {tweet_id}")
                
            except tweepy.TweepyException as e:
                logger.error(f"Error posting thread tweet {i+1}: {e}")
                break
        
        if tweet_ids and not dry_run:
            self._increment_daily_count()
        
        return tweet_ids
    
    def get_stats(self) -> dict:
        """Tweet istatistiklerini getir"""
        history = self._load_history()
        today = datetime.now().strftime("%Y-%m-%d")
        
        return {
            "total_tweets": len(history.get("tweets", [])),
            "today_count": history.get("daily_count", {}).get(today, 0),
            "daily_limit": config.tweet.max_daily_tweets,
            "remaining_today": config.tweet.max_daily_tweets - history.get("daily_count", {}).get(today, 0)
        }


# Test için
if __name__ == "__main__":
    from loguru import logger
    import sys
    
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    poster = XPoster()
    
    # İstatistikler
    print("\n=== Tweet Stats ===")
    stats = poster.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Kuru test
    print("\n=== Dry Run Test ===")
    test_tweet = "🔥 Bu bir test tweet'idir. Otomasyon çalışıyor! #test"
    result = poster.post_tweet(test_tweet, "tr", dry_run=True)
    print(f"Result: {result}")
