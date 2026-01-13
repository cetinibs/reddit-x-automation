"""
X Engagement Manager - Hurricane Notları Stratejisi
%90 Quote/Mention, %10 Orijinal Post yaklaşımı
Büyük hesaplardan trustscore aktarımı
"""
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from loguru import logger
import tweepy

from config import config, DATA_DIR


class XEngagementManager:
    """
    X (Twitter) etkileşim yöneticisi
    
    Hurricane Stratejisi:
    - %90 quote tweet ve mention (reply)
    - %10 orijinal post
    - Büyük hesaplara etkileşim = trustscore aktarımı
    - 24 saat kuralı: Sessizlik = negatif boost
    """
    
    def __init__(self):
        self.client = self._create_client()
        self.engagement_file = DATA_DIR / "engagement_history.json"
        self.target_accounts_file = DATA_DIR / "target_accounts.json"
        self.last_activity_file = DATA_DIR / "last_activity.json"
    
    def _create_client(self) -> tweepy.Client:
        """Tweepy client oluştur"""
        return tweepy.Client(
            consumer_key=config.x.api_key,
            consumer_secret=config.x.api_secret,
            access_token=config.x.access_token,
            access_token_secret=config.x.access_token_secret,
            bearer_token=config.x.bearer_token
        )
    
    def _load_engagement_history(self) -> dict:
        """Engagement geçmişini yükle"""
        if self.engagement_file.exists():
            try:
                return json.loads(self.engagement_file.read_text())
            except:
                return {"quotes": [], "mentions": [], "replies": [], "daily_stats": {}}
        return {"quotes": [], "mentions": [], "replies": [], "daily_stats": {}}
    
    def _save_engagement_history(self, history: dict):
        """Engagement geçmişini kaydet"""
        self.engagement_file.write_text(json.dumps(history, indent=2, ensure_ascii=False))
    
    def _update_last_activity(self):
        """Son aktivite zamanını güncelle"""
        self.last_activity_file.write_text(json.dumps({
            "last_activity": datetime.now().isoformat(),
            "type": "engagement"
        }, indent=2))
    
    def check_24h_rule(self) -> tuple[bool, float]:
        """
        24 saat kuralını kontrol et
        
        Returns:
            (is_urgent, hours_since_last): Acil mi ve son aktiviteden bu yana geçen saat
        """
        if not self.last_activity_file.exists():
            return True, 999  # Hiç aktivite yok, acil
        
        try:
            data = json.loads(self.last_activity_file.read_text())
            last_activity = datetime.fromisoformat(data["last_activity"])
            hours_since = (datetime.now() - last_activity).total_seconds() / 3600
            
            # 23 saatten fazla sessizlik = acil
            is_urgent = hours_since >= config.engagement.max_silence_hours
            
            if is_urgent:
                logger.warning(f"⚠️ 24 saat kuralı! Son aktiviteden {hours_since:.1f} saat geçti!")
            
            return is_urgent, hours_since
        except:
            return True, 999
    
    def load_target_accounts(self) -> List[Dict]:
        """
        Hedef büyük hesapları yükle
        
        Trustscore aktarımı için takip edilecek hesaplar
        """
        if self.target_accounts_file.exists():
            try:
                return json.loads(self.target_accounts_file.read_text())
            except:
                return []
        return []
    
    def add_target_account(self, username: str, category: str = "general"):
        """Hedef hesap ekle"""
        accounts = self.load_target_accounts()
        
        # Zaten var mı kontrol et
        if any(a["username"] == username for a in accounts):
            logger.info(f"Hesap zaten listede: @{username}")
            return
        
        accounts.append({
            "username": username,
            "category": category,
            "added_at": datetime.now().isoformat(),
            "engagement_count": 0
        })
        
        self.target_accounts_file.write_text(json.dumps(accounts, indent=2, ensure_ascii=False))
        logger.info(f"Hedef hesap eklendi: @{username} ({category})")
    
    def get_user_recent_tweets(self, username: str, count: int = 10) -> List[Dict]:
        """
        Kullanıcının son tweetlerini getir
        
        Quote veya reply için tweet seçimi
        """
        try:
            # Kullanıcı ID'sini al
            user = self.client.get_user(username=username)
            if not user.data:
                logger.warning(f"Kullanıcı bulunamadı: @{username}")
                return []
            
            user_id = user.data.id
            
            # Son tweetleri al
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=count,
                tweet_fields=["created_at", "public_metrics", "conversation_id"]
            )
            
            if not tweets.data:
                return []
            
            return [
                {
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "metrics": tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
                }
                for tweet in tweets.data
            ]
            
        except Exception as e:
            logger.error(f"Tweet çekme hatası (@{username}): {e}")
            return []
    
    def quote_tweet(
        self, 
        tweet_id: str, 
        comment: str, 
        dry_run: bool = None
    ) -> Optional[str]:
        """
        Quote tweet yap (Alıntı tweet)
        
        Hurricane: Büyük hesapları quote'layarak trustscore aktar
        
        Args:
            tweet_id: Alıntılanacak tweet ID'si
            comment: Alıntı yorumu
            dry_run: Test modu
            
        Returns:
            Yeni tweet ID veya None
        """
        dry_run = dry_run if dry_run is not None else config.dry_run
        
        if len(comment) > 280:
            logger.warning(f"Quote çok uzun ({len(comment)} karakter), kırpılıyor...")
            comment = comment[:277] + "..."
        
        if dry_run:
            logger.info(f"[DRY RUN] Quote tweet: {comment[:50]}... -> Tweet {tweet_id}")
            return "dry_run_quote_id"
        
        try:
            # Quote tweet = tweet metnine URL ekleyerek
            tweet_url = f"https://twitter.com/i/status/{tweet_id}"
            full_text = f"{comment}\n\n{tweet_url}"
            
            if len(full_text) > 280:
                # URL için yer bırak (23 karakter + newlines)
                max_comment = 280 - 25 - 3
                comment = comment[:max_comment] + "..."
                full_text = f"{comment}\n\n{tweet_url}"
            
            response = self.client.create_tweet(text=full_text)
            quote_id = response.data["id"]
            
            # Geçmişe kaydet
            history = self._load_engagement_history()
            history["quotes"].append({
                "quote_id": quote_id,
                "original_tweet_id": tweet_id,
                "comment": comment,
                "created_at": datetime.now().isoformat()
            })
            self._save_engagement_history(history)
            self._update_last_activity()
            
            logger.success(f"Quote tweet oluşturuldu: {quote_id}")
            return quote_id
            
        except tweepy.TweepyException as e:
            logger.error(f"Quote tweet hatası: {e}")
            return None
    
    def reply_to_tweet(
        self, 
        tweet_id: str, 
        reply_text: str, 
        dry_run: bool = None
    ) -> Optional[str]:
        """
        Tweet'e yanıt ver (Mention)
        
        Hurricane: Büyük hesaplara yanıt = trustscore aktarımı
        
        Args:
            tweet_id: Yanıtlanacak tweet ID'si
            reply_text: Yanıt metni
            dry_run: Test modu
            
        Returns:
            Yanıt tweet ID veya None
        """
        dry_run = dry_run if dry_run is not None else config.dry_run
        
        if len(reply_text) > 280:
            logger.warning(f"Reply çok uzun ({len(reply_text)} karakter), kırpılıyor...")
            reply_text = reply_text[:277] + "..."
        
        if dry_run:
            logger.info(f"[DRY RUN] Reply: {reply_text[:50]}... -> Tweet {tweet_id}")
            return "dry_run_reply_id"
        
        try:
            response = self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=tweet_id
            )
            reply_id = response.data["id"]
            
            # Geçmişe kaydet
            history = self._load_engagement_history()
            history["replies"].append({
                "reply_id": reply_id,
                "original_tweet_id": tweet_id,
                "text": reply_text,
                "created_at": datetime.now().isoformat()
            })
            self._save_engagement_history(history)
            self._update_last_activity()
            
            logger.success(f"Reply oluşturuldu: {reply_id}")
            return reply_id
            
        except tweepy.TweepyException as e:
            logger.error(f"Reply hatası: {e}")
            return None
    
    def mention_user(
        self, 
        username: str, 
        tweet_text: str, 
        dry_run: bool = None
    ) -> Optional[str]:
        """
        Kullanıcıyı mention et (yeni tweet'te)
        
        Args:
            username: Mention edilecek kullanıcı (@'sız)
            tweet_text: Tweet metni (@username otomatik eklenir)
            dry_run: Test modu
            
        Returns:
            Tweet ID veya None
        """
        dry_run = dry_run if dry_run is not None else config.dry_run
        
        # Mention ekle
        full_text = f"@{username} {tweet_text}"
        
        if len(full_text) > 280:
            max_text = 280 - len(username) - 2
            tweet_text = tweet_text[:max_text - 3] + "..."
            full_text = f"@{username} {tweet_text}"
        
        if dry_run:
            logger.info(f"[DRY RUN] Mention @{username}: {tweet_text[:50]}...")
            return "dry_run_mention_id"
        
        try:
            response = self.client.create_tweet(text=full_text)
            mention_id = response.data["id"]
            
            # Geçmişe kaydet
            history = self._load_engagement_history()
            history["mentions"].append({
                "mention_id": mention_id,
                "mentioned_user": username,
                "text": tweet_text,
                "created_at": datetime.now().isoformat()
            })
            self._save_engagement_history(history)
            self._update_last_activity()
            
            logger.success(f"Mention oluşturuldu: {mention_id}")
            return mention_id
            
        except tweepy.TweepyException as e:
            logger.error(f"Mention hatası: {e}")
            return None
    
    def get_daily_engagement_stats(self) -> dict:
        """Günlük engagement istatistikleri"""
        history = self._load_engagement_history()
        today = datetime.now().strftime("%Y-%m-%d")
        
        today_quotes = [q for q in history.get("quotes", []) 
                       if q.get("created_at", "").startswith(today)]
        today_replies = [r for r in history.get("replies", []) 
                        if r.get("created_at", "").startswith(today)]
        today_mentions = [m for m in history.get("mentions", []) 
                         if m.get("created_at", "").startswith(today)]
        
        total_engagement = len(today_quotes) + len(today_replies) + len(today_mentions)
        
        return {
            "date": today,
            "quotes": len(today_quotes),
            "replies": len(today_replies),
            "mentions": len(today_mentions),
            "total": total_engagement,
            "quote_target": config.engagement.daily_quote_target,
            "mention_target": config.engagement.daily_mention_target,
            "quote_remaining": max(0, config.engagement.daily_quote_target - len(today_quotes)),
            "mention_remaining": max(0, config.engagement.daily_mention_target - len(today_mentions))
        }
    
    def decide_action_type(self) -> str:
        """
        Hangi aksiyon türü alınacağını belirle
        
        Hurricane: %90 quote/mention, %10 orijinal
        
        Returns:
            'quote', 'reply', 'mention', veya 'original'
        """
        roll = random.random()
        
        if roll < config.engagement.quote_mention_ratio:
            # %90: Quote veya mention
            sub_roll = random.random()
            if sub_roll < 0.5:
                return "quote"
            elif sub_roll < 0.8:
                return "reply"
            else:
                return "mention"
        else:
            # %10: Orijinal post
            return "original"
    
    def select_target_for_engagement(self) -> Optional[Dict]:
        """
        Engagement için hedef hesap seç
        
        En az etkileşim yapılmış hesaba öncelik ver
        """
        accounts = self.load_target_accounts()
        
        if not accounts:
            logger.warning("Hedef hesap listesi boş!")
            return None
        
        # En az etkileşim yapılana öncelik
        accounts.sort(key=lambda x: x.get("engagement_count", 0))
        
        return accounts[0]
    
    def increment_engagement_count(self, username: str):
        """Hesabın engagement sayısını artır"""
        accounts = self.load_target_accounts()
        
        for account in accounts:
            if account["username"] == username:
                account["engagement_count"] = account.get("engagement_count", 0) + 1
                break
        
        self.target_accounts_file.write_text(json.dumps(accounts, indent=2, ensure_ascii=False))


# Test için
if __name__ == "__main__":
    from loguru import logger
    import sys
    
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    manager = XEngagementManager()
    
    # 24 saat kuralı kontrolü
    print("\n=== 24 Saat Kuralı ===")
    is_urgent, hours = manager.check_24h_rule()
    print(f"Acil: {is_urgent}, Son aktiviteden: {hours:.1f} saat")
    
    # Günlük statistikler
    print("\n=== Günlük Engagement ===")
    stats = manager.get_daily_engagement_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Aksiyon kararı
    print("\n=== Aksiyon Kararları (10 örnek) ===")
    for i in range(10):
        action = manager.decide_action_type()
        print(f"{i+1}. {action}")
