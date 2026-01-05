#!/usr/bin/env python3
"""
Scheduler - Otomatik zamanlayıcı
Belirlenen saatlerde tweet paylaşımı yapar
"""
import sys
import signal
import time
from datetime import datetime
from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import config, LOGS_DIR
from main import run_automation, setup_logging


class TweetScheduler:
    """Tweet zamanlayıcısı"""
    
    def __init__(self):
        self.timezone = pytz.timezone(config.schedule.timezone)
        self.scheduler = BlockingScheduler(timezone=self.timezone)
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
    
    def _shutdown(self, signum, frame):
        """Güvenli kapanış"""
        logger.info("Shutting down scheduler...")
        self.scheduler.shutdown(wait=False)
        sys.exit(0)
    
    def _parse_time(self, time_str: str) -> tuple:
        """Saat:dakika formatını parse et"""
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])
    
    def add_schedule(self, time_str: str, language: str, job_id: str = None):
        """
        Zamanlanmış görev ekle
        
        Args:
            time_str: Saat formatı (HH:MM)
            language: Tweet dili
            job_id: Görev ID'si
        """
        hour, minute = self._parse_time(time_str)
        job_id = job_id or f"tweet_{language}_{time_str.replace(':', '')}"
        
        self.scheduler.add_job(
            run_automation,
            CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
            kwargs={"language": language, "dry_run": config.dry_run},
            id=job_id,
            name=f"Tweet ({language.upper()}) at {time_str}",
            replace_existing=True
        )
        
        logger.info(f"Scheduled: {language.upper()} tweet at {time_str} ({config.schedule.timezone})")
    
    def setup_default_schedule(self):
        """Varsayılan zamanlamayı kur"""
        logger.info("Setting up default schedule...")
        
        # Türkçe tweet'ler
        for time_str in config.schedule.schedule_tr:
            self.add_schedule(time_str, "tr")
        
        # İngilizce tweet'ler
        for time_str in config.schedule.schedule_en:
            self.add_schedule(time_str, "en")
        
        logger.info(f"Total scheduled jobs: {len(self.scheduler.get_jobs())}")
    
    def list_jobs(self):
        """Zamanlanmış görevleri listele"""
        jobs = self.scheduler.get_jobs()
        
        print("\n📅 Zamanlanmış Görevler")
        print("=" * 50)
        
        if not jobs:
            print("Henüz zamanlanmış görev yok.")
            return
        
        for job in jobs:
            next_run = job.next_run_time
            if next_run:
                next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S %Z")
            else:
                next_run_str = "N/A"
            
            print(f"• {job.name}")
            print(f"  ID: {job.id}")
            print(f"  Next run: {next_run_str}")
            print()
    
    def run_now(self, language: str = "tr"):
        """Hemen çalıştır (test için)"""
        logger.info(f"Running immediately ({language.upper()})...")
        run_automation(language=language)
    
    def start(self):
        """Zamanlayıcıyı başlat"""
        logger.info(f"Starting scheduler (timezone: {config.schedule.timezone})...")
        logger.info("Press Ctrl+C to exit")
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Tweet Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python scheduler.py                  # Zamanlayıcıyı başlat
  python scheduler.py --list           # Görevleri listele
  python scheduler.py --run-now tr     # Hemen Türkçe tweet at
  python scheduler.py --run-now en     # Hemen İngilizce tweet at
        """
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Zamanlanmış görevleri listele"
    )
    
    parser.add_argument(
        "--run-now", "-r",
        choices=["tr", "en"],
        help="Hemen belirtilen dilde tweet at"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Detaylı log çıktısı"
    )
    
    args = parser.parse_args()
    
    # Logging
    log_level = "DEBUG" if args.verbose else config.log_level
    setup_logging(log_level)
    
    # Scheduler oluştur
    scheduler = TweetScheduler()
    scheduler.setup_default_schedule()
    
    if args.list:
        scheduler.list_jobs()
        return
    
    if args.run_now:
        scheduler.run_now(args.run_now)
        return
    
    # Başlat
    scheduler.start()


if __name__ == "__main__":
    main()
