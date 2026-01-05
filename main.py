#!/usr/bin/env python3
"""
Reddit → X Automation - Ana Orkestrasyon
Reddit'ten popüler konuları alıp X'te paylaşır
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


def run_automation(
    language: str = "tr",
    dry_run: bool = False,
    thread_mode: bool = False
):
    """
    Ana otomasyon döngüsü
    
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
        description="Reddit → X Automation Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python main.py --lang tr              # Türkçe tweet at
  python main.py --lang en              # İngilizce tweet at
  python main.py --lang tr --dry-run    # Test (tweet atmadan)
  python main.py --lang en --thread     # İngilizce thread at
  python main.py --stats                # İstatistikleri göster
        """
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
        "--verbose", "-v",
        action="store_true",
        help="Detaylı log çıktısı"
    )
    
    args = parser.parse_args()
    
    # Logging setup
    log_level = "DEBUG" if args.verbose else config.log_level
    setup_logging(log_level)
    
    # İstatistikler modu
    if args.stats:
        poster = XPoster()
        stats = poster.get_stats()
        
        print("\n📊 Tweet İstatistikleri")
        print("=" * 30)
        print(f"Toplam tweet: {stats['total_tweets']}")
        print(f"Bugün: {stats['today_count']}/{stats['daily_limit']}")
        print(f"Kalan: {stats['remaining_today']}")
        return
    
    # Ana otomasyon
    try:
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
