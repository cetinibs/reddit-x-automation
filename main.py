#!/usr/bin/env python3
"""
Reddit → X Automation - Hurricane Stratejisi ile Ana Orkestrasyon
%90 Quote/Mention, %10 Orijinal Post yaklaşımı
"""
import sys
import argparse
from datetime import datetime
from pathlib import Path
from loguru import logger

from config import config, LOGS_DIR
from reddit_scraper import RedditScraper
from tweet_generator import TweetGenerator
from x_poster import XPoster
from x_engagement import XEngagementManager


def setup_logging(level: str = "INFO"):
    """Logging yapılandır"""
    logger.remove()
    
    # Console output
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    )
    
    # File output
    log_file = LOGS_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="1 day",
        retention="7 days"
    )


def run_engagement(
    language: str = "tr",
    dry_run: bool = False
):
    """
    Hurricane Engagement Modu
    
    Büyük hesaplara quote/mention yaparak trustscore artır
    %90 engagement, %10 orijinal post
    """
    logger.info(f"{'='*50}")
    logger.info(f"🌀 Hurricane Engagement Mode")
    logger.info(f"Language: {language.upper()}")
    logger.info(f"Dry Run: {dry_run}")
    logger.info(f"{'='*50}")
    
    engagement = XEngagementManager()
    generator = TweetGenerator()
    
    # 24 saat kuralı kontrolü
    is_urgent, hours_since = engagement.check_24h_rule()
    if is_urgent:
        logger.warning(f"⚠️ ACİL: {hours_since:.1f} saat aktivite yok! Hemen aksiyon alınmalı!")
    
    # Günlük istatistikler
    stats = engagement.get_daily_engagement_stats()
    logger.info(f"Bugünkü engagement: {stats['total']} (Quote: {stats['quotes']}, Reply: {stats['replies']}, Mention: {stats['mentions']})")
    
    # Hangi aksiyon türü?
    action_type = engagement.decide_action_type()
    logger.info(f"Aksiyon türü: {action_type}")
    
    if action_type == "original":
        # Orijinal post modu - mevcut akışı kullan
        logger.info("Orijinal post moduna geçiliyor...")
        return run_automation(language, dry_run, thread_mode=False)
    
    # Engagement modu - hedef hesap seç
    target = engagement.select_target_for_engagement()
    
    if not target:
        logger.warning("Hedef hesap bulunamadı! Önce hedef hesap ekleyin:")
        logger.info("python main.py --add-target <username>")
        return False
    
    username = target["username"]
    logger.info(f"Hedef hesap: @{username}")
    
    # Hesabın son tweetlerini al
    tweets = engagement.get_user_recent_tweets(username, count=5)
    
    if not tweets:
        logger.warning(f"@{username} için tweet bulunamadı")
        return False
    
    # En uygun tweeti seç (en yeni ve etkileşimli)
    selected_tweet = tweets[0]
    logger.info(f"Seçilen tweet: {selected_tweet['text'][:50]}...")
    
    if action_type == "quote":
        # Quote tweet
        comment = generator.generate_quote_comment(selected_tweet["text"], language)
        if comment:
            result = engagement.quote_tweet(selected_tweet["id"], comment, dry_run=dry_run)
            if result:
                engagement.increment_engagement_count(username)
                logger.success(f"Quote tweet başarılı! ID: {result}")
                return True
    
    elif action_type == "reply":
        # Reply
        reply = generator.generate_reply(selected_tweet["text"], language)
        if reply:
            result = engagement.reply_to_tweet(selected_tweet["id"], reply, dry_run=dry_run)
            if result:
                engagement.increment_engagement_count(username)
                logger.success(f"Reply başarılı! ID: {result}")
                return True
    
    elif action_type == "mention":
        # Direct mention
        mention_text = generator.generate_reply(selected_tweet["text"], language)
        if mention_text:
            result = engagement.mention_user(username, mention_text, dry_run=dry_run)
            if result:
                engagement.increment_engagement_count(username)
                logger.success(f"Mention başarılı! ID: {result}")
                return True
    
    logger.error("Engagement başarısız")
    return False


def run_automation(
    language: str = "tr",
    dry_run: bool = False,
    thread_mode: bool = False
):
    """
    Ana otomasyon döngüsü (Orijinal post modu)
    
    Args:
        language: Tweet dili ('tr' veya 'en')
        dry_run: Kuru çalıştırma (tweet atmadan test)
        thread_mode: Thread mi yoksa tek tweet mi
    """
    logger.info(f"{'='*50}")
    logger.info(f"Reddit → X Automation Started")
    logger.info(f"Language: {language.upper()}")
    logger.info(f"Dry Run: {dry_run}")
    logger.info(f"Thread Mode: {thread_mode}")
    logger.info(f"{'='*50}")
    
    # Bileşenleri oluştur
    scraper = RedditScraper()
    generator = TweetGenerator()
    poster = XPoster()
    
    # Limit kontrolü
    can_post, reason = poster.can_post()
    if not can_post and not dry_run:
        logger.warning(f"Skipping: {reason}")
        return False
    
    # Mevcut istatistikler
    stats = poster.get_stats()
    logger.info(f"Today's tweets: {stats['today_count']}/{stats['daily_limit']}")
    
    # Reddit'ten popüler post al
    logger.info("Fetching top Reddit post...")
    post = scraper.get_top_post()
    
    if not post:
        logger.warning("No suitable posts found")
        return False
    
    logger.info(f"Selected: [{post.subreddit}] {post.title[:60]}...")
    logger.info(f"Score: {post.score} | Comments: {post.num_comments}")
    
    if thread_mode:
        # Thread oluştur
        logger.info("Generating thread...")
        tweets = generator.generate_thread(post, language, tweet_count=5)
        
        if not tweets:
            logger.error("Failed to generate thread")
            return False
        
        logger.info(f"Generated {len(tweets)} tweets for thread")
        
        # Thread paylaş
        tweet_ids = poster.post_thread(tweets, language, dry_run=dry_run)
        
        if tweet_ids:
            logger.success(f"Thread posted! First tweet ID: {tweet_ids[0]}")
            if not dry_run:
                scraper.mark_as_posted(post.id)
            return True
    else:
        # Tek tweet oluştur
        logger.info("Generating tweet...")
        tweet_text = generator.generate_tweet(post, language)
        
        if not tweet_text:
            logger.error("Failed to generate tweet")
            return False
        
        logger.info(f"Generated tweet ({len(tweet_text)} chars)")
        logger.debug(f"Tweet: {tweet_text}")
        
        # Tweet paylaş
        tweet_id = poster.post_tweet(
            tweet_text, 
            language, 
            reddit_post_id=post.id,
            dry_run=dry_run
        )
        
        if tweet_id:
            logger.success(f"Tweet posted! ID: {tweet_id}")
            if not dry_run:
                scraper.mark_as_posted(post.id)
            return True
    
    logger.error("Failed to post")
    return False


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Reddit → X Automation Bot (Hurricane Stratejisi)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🌀 Hurricane Stratejisi:
  - %90 Quote/Mention (büyük hesaplara etkileşim)
  - %10 Orijinal post (Reddit'ten içerik)
  - 24 saat kuralı (sessizlik = negatif boost)
  - Trustscore aktarımı

Örnekler:
  python main.py --engage                    # Hurricane engagement modu
  python main.py --lang tr                   # Türkçe tweet at
  python main.py --lang en --dry-run         # Test (tweet atmadan)
  python main.py --add-target elonmusk       # Hedef hesap ekle
  python main.py --check-24h                 # 24 saat kuralı kontrolü
  python main.py --stats                     # İstatistikleri göster
        """
    )
    
    parser.add_argument(
        "--engage", "-e",
        action="store_true",
        help="Hurricane engagement modu (quote/mention)"
    )
    
    parser.add_argument(
        "--lang", "-l",
        choices=["tr", "en"],
        default=config.default_language,
        help="Tweet dili (varsayılan: tr)"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Kuru çalıştırma (tweet atmadan test)"
    )
    
    parser.add_argument(
        "--thread", "-t",
        action="store_true",
        help="Thread modunda çalıştır"
    )
    
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="İstatistikleri göster ve çık"
    )
    
    parser.add_argument(
        "--add-target",
        metavar="USERNAME",
        help="Hedef hesap ekle (engagement için)"
    )
    
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="Hedef hesapları listele"
    )
    
    parser.add_argument(
        "--check-24h",
        action="store_true",
        help="24 saat kuralını kontrol et"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Detaylı log çıktısı"
    )
    
    args = parser.parse_args()
    
    # Logging setup
    log_level = "DEBUG" if args.verbose else config.log_level
    setup_logging(log_level)
    
    # Hedef hesap ekleme
    if args.add_target:
        engagement = XEngagementManager()
        engagement.add_target_account(args.add_target)
        print(f"✅ Hedef hesap eklendi: @{args.add_target}")
        return
    
    # Hedef hesapları listeleme
    if args.list_targets:
        engagement = XEngagementManager()
        targets = engagement.load_target_accounts()
        
        print("\n🎯 Hedef Hesaplar")
        print("=" * 40)
        if not targets:
            print("Henüz hedef hesap yok.")
            print("Eklemek için: python main.py --add-target <username>")
        else:
            for t in targets:
                print(f"• @{t['username']} ({t.get('category', 'general')})")
                print(f"  Engagement: {t.get('engagement_count', 0)}")
        return
    
    # 24 saat kuralı kontrolü
    if args.check_24h:
        engagement = XEngagementManager()
        is_urgent, hours = engagement.check_24h_rule()
        
        print("\n⏰ 24 Saat Kuralı Kontrolü")
        print("=" * 40)
        print(f"Son aktiviteden bu yana: {hours:.1f} saat")
        if is_urgent:
            print("⚠️ ACİL: 24 saat kuralı! Hemen etkileşim yapmalısınız!")
        else:
            remaining = config.engagement.max_silence_hours - hours
            print(f"✅ OK. Kalan süre: {remaining:.1f} saat")
        return
    
    # İstatistikler modu
    if args.stats:
        poster = XPoster()
        engagement = XEngagementManager()
        
        tweet_stats = poster.get_stats()
        engagement_stats = engagement.get_daily_engagement_stats()
        
        print("\n📊 Tweet İstatistikleri")
        print("=" * 40)
        print(f"Toplam tweet: {tweet_stats['total_tweets']}")
        print(f"Bugün: {tweet_stats['today_count']}/{tweet_stats['daily_limit']}")
        print(f"Kalan: {tweet_stats['remaining_today']}")
        
        print("\n🌀 Engagement İstatistikleri")
        print("=" * 40)
        print(f"Quote: {engagement_stats['quotes']}/{engagement_stats['quote_target']}")
        print(f"Reply: {engagement_stats['replies']}")
        print(f"Mention: {engagement_stats['mentions']}/{engagement_stats['mention_target']}")
        print(f"Toplam: {engagement_stats['total']}")
        
        # 24 saat kontrolü
        is_urgent, hours = engagement.check_24h_rule()
        print(f"\n⏰ Son aktivite: {hours:.1f} saat önce")
        if is_urgent:
            print("⚠️ ACİL: 24 saat kuralı!")
        return
    
    # Ana otomasyon
    try:
        if args.engage:
            # Hurricane engagement modu
            success = run_engagement(
                language=args.lang,
                dry_run=args.dry_run or config.dry_run
            )
        else:
            # Orijinal post modu
            success = run_automation(
                language=args.lang,
                dry_run=args.dry_run or config.dry_run,
                thread_mode=args.thread
            )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
