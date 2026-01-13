#!/usr/bin/env python3
"""
Scheduler - Hurricane Stratejisi ile Otomatik Zamanlayıcı
%90 Engagement, %10 Orijinal Post - 24 Saat Kuralı
"""
import sys
import signal
import time
import random
from datetime import datetime
from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from config import config, LOGS_DIR
from main import run_automation, run_engagement, setup_logging
from x_engagement import XEngagementManager


class TweetScheduler:
    """
    Hurricane Tweet Zamanlayıcısı
    
    Strateji:
    - %90 engagement (quote/mention) - daha sık
    - %10 orijinal post (Reddit'ten) - daha seyrek
    - 24 saat kuralı: Maksimum 23 saat sessizlik
    """
    
    def __init__(self):
        self.timezone = pytz.timezone(config.schedule.timezone)
        self.scheduler = BlockingScheduler(timezone=self.timezone)
        self.engagement_manager = XEngagementManager()
        
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
    
    def _run_hurricane_cycle(self, language: str):
        """
        Hurricane döngüsü - aksiyon türünü otomatik seç
        
        %90 engagement, %10 orijinal
        """
        logger.info(f"🌀 Hurricane cycle başladı ({language.upper()})")
        
        # 24 saat kuralı kontrolü
        is_urgent, hours = self.engagement_manager.check_24h_rule()
        
        if is_urgent:
            logger.warning(f"⚠️ 24 saat kuralı aktif! Acil aksiyon alınıyor...")
            # Acil durumda engagement yap
            run_engagement(language=language, dry_run=config.dry_run)
            return
        
        # Normal akış - rastgele karar
        action_type = self.engagement_manager.decide_action_type()
        logger.info(f"Seçilen aksiyon: {action_type}")
        
        if action_type == "original":
            run_automation(language=language, dry_run=config.dry_run)
        else:
            run_engagement(language=language, dry_run=config.dry_run)
    
    def add_engagement_schedule(self, time_str: str, language: str, job_id: str = None):
        """
        Engagement zamanlaması ekle (quote/mention)
        
        Hurricane: Sık engagement yapılmalı
        """
        hour, minute = self._parse_time(time_str)
        job_id = job_id or f"engage_{language}_{time_str.replace(':', '')}"
        
        self.scheduler.add_job(
            run_engagement,
            CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
            kwargs={"language": language, "dry_run": config.dry_run},
            id=job_id,
            name=f"🌀 Engage ({language.upper()}) at {time_str}",
            replace_existing=True
        )
        
        logger.info(f"Scheduled engagement: {language.upper()} at {time_str}")
    
    def add_original_schedule(self, time_str: str, language: str, job_id: str = None):
        """
        Orijinal post zamanlaması ekle (Reddit'ten)
        
        Hurricane: Daha seyrek orijinal post
        """
        hour, minute = self._parse_time(time_str)
        job_id = job_id or f"tweet_{language}_{time_str.replace(':', '')}"
        
        self.scheduler.add_job(
            run_automation,
            CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
            kwargs={"language": language, "dry_run": config.dry_run},
            id=job_id,
            name=f"📝 Tweet ({language.upper()}) at {time_str}",
            replace_existing=True
        )
        
        logger.info(f"Scheduled original post: {language.upper()} at {time_str}")
    
    def add_hurricane_schedule(self, time_str: str, language: str, job_id: str = None):
        """
        Hurricane döngüsü zamanlaması (%90/%10 otomatik karar)
        """
        hour, minute = self._parse_time(time_str)
        job_id = job_id or f"hurricane_{language}_{time_str.replace(':', '')}"
        
        self.scheduler.add_job(
            self._run_hurricane_cycle,
            CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
            kwargs={"language": language},
            id=job_id,
            name=f"🌀 Hurricane ({language.upper()}) at {time_str}",
            replace_existing=True
        )
        
        logger.info(f"Scheduled Hurricane cycle: {language.upper()} at {time_str}")
    
    def add_24h_check(self):
        """
        24 saat kuralı kontrolü - her 4 saatte bir
        
        Eğer sessizlik 20 saati geçtiyse uyarı ver
        """
        def check_and_alert():
            is_urgent, hours = self.engagement_manager.check_24h_rule()
            
            if hours >= 20:
                logger.warning(f"⚠️ UYARI: {hours:.1f} saat aktivite yok!")
                logger.warning("24 saat kuralına yaklaşılıyor!")
                
                if is_urgent:
                    logger.error("🚨 ACİL: Şimdi aksiyon alınmalı!")
                    # Otomatik engagement yap
                    run_engagement(language=config.default_language, dry_run=config.dry_run)
        
        self.scheduler.add_job(
            check_and_alert,
            IntervalTrigger(hours=4, timezone=self.timezone),
            id="check_24h_rule",
            name="⏰ 24h Rule Check",
            replace_existing=True
        )
        
        logger.info("Scheduled 24h rule check every 4 hours")
    
    def setup_hurricane_schedule(self):
        """
        Hurricane stratejisi zamanlamasını kur
        
        - Engagement: Günde 8 kez (3 saatte 1)
        - Orijinal post: Günde 2-3 kez
        - 24 saat kontrolü: 4 saatte 1
        """
        logger.info("🌀 Setting up Hurricane schedule...")
        
        # Engagement zamanları (Türkçe)
        for time_str in config.schedule.engagement_schedule:
            self.add_engagement_schedule(time_str, "tr")
        
        # Orijinal post zamanları (Türkçe)
        for time_str in config.schedule.schedule_tr:
            self.add_original_schedule(time_str, "tr")
        
        # İngilizce orijinal postlar
        for time_str in config.schedule.schedule_en:
            self.add_original_schedule(time_str, "en")
        
        # 24 saat kuralı kontrolü
        self.add_24h_check()
        
        logger.info(f"Total scheduled jobs: {len(self.scheduler.get_jobs())}")
    
    def setup_default_schedule(self):
        """Eski varsayılan zamanlama (geriye uyumluluk)"""
        logger.info("Setting up default schedule...")
        
        # Türkçe tweet'ler
        for time_str in config.schedule.schedule_tr:
            self.add_original_schedule(time_str, "tr")
        
        # İngilizce tweet'ler
        for time_str in config.schedule.schedule_en:
            self.add_original_schedule(time_str, "en")
        
        logger.info(f"Total scheduled jobs: {len(self.scheduler.get_jobs())}")
    
    def list_jobs(self):
        """Zamanlanmış görevleri listele"""
        jobs = self.scheduler.get_jobs()
        
        print("\n📅 Zamanlanmış Görevler")
        print("=" * 60)
        
        if not jobs:
            print("Henüz zamanlanmış görev yok.")
            return
        
        # Grupla
        engagement_jobs = [j for j in jobs if "Engage" in j.name or "Hurricane" in j.name]
        tweet_jobs = [j for j in jobs if "Tweet" in j.name]
        other_jobs = [j for j in jobs if j not in engagement_jobs and j not in tweet_jobs]
        
        if engagement_jobs:
            print("\n🌀 Engagement Görevleri:")
            for job in engagement_jobs:
                next_run = job.next_run_time
                next_run_str = next_run.strftime("%Y-%m-%d %H:%M") if next_run else "N/A"
                print(f"  • {job.name} → Sonraki: {next_run_str}")
        
        if tweet_jobs:
            print("\n📝 Orijinal Tweet Görevleri:")
            for job in tweet_jobs:
                next_run = job.next_run_time
                next_run_str = next_run.strftime("%Y-%m-%d %H:%M") if next_run else "N/A"
                print(f"  • {job.name} → Sonraki: {next_run_str}")
        
        if other_jobs:
            print("\n⚙️ Diğer Görevler:")
            for job in other_jobs:
                next_run = job.next_run_time
                next_run_str = next_run.strftime("%Y-%m-%d %H:%M") if next_run else "N/A"
                print(f"  • {job.name} → Sonraki: {next_run_str}")
    
    def run_now(self, language: str = "tr", mode: str = "hurricane"):
        """
        Hemen çalıştır
        
        Args:
            language: Dil
            mode: 'hurricane', 'engage', veya 'original'
        """
        logger.info(f"Running immediately ({language.upper()}, mode={mode})...")
        
        if mode == "hurricane":
            self._run_hurricane_cycle(language)
        elif mode == "engage":
            run_engagement(language=language)
        else:
            run_automation(language=language)
    
    def start(self, hurricane_mode: bool = True):
        """
        Zamanlayıcıyı başlat
        
        Args:
            hurricane_mode: True = Hurricane stratejisi, False = Eski mod
        """
        if hurricane_mode:
            self.setup_hurricane_schedule()
        else:
            self.setup_default_schedule()
        
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
        description="Hurricane Tweet Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🌀 Hurricane Stratejisi:
  - Engagement (quote/mention): Günde 8 kez
  - Orijinal post (Reddit): Günde 2-3 kez
  - 24 saat kuralı kontrolü: 4 saatte 1

Örnekler:
  python scheduler.py                  # Hurricane modunda başlat
  python scheduler.py --classic        # Eski modu kullan
  python scheduler.py --list           # Görevleri listele
  python scheduler.py --run-now tr     # Hemen çalıştır
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
        help="Hemen belirtilen dilde çalıştır"
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["hurricane", "engage", "original"],
        default="hurricane",
        help="Çalıştırma modu (varsayılan: hurricane)"
    )
    
    parser.add_argument(
        "--classic",
        action="store_true",
        help="Eski mod (Hurricane stratejisi olmadan)"
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
    
    if args.list:
        # Hurricane modunda zamanlamayı kur ve listele
        if not args.classic:
            scheduler.setup_hurricane_schedule()
        else:
            scheduler.setup_default_schedule()
        scheduler.list_jobs()
        return
    
    if args.run_now:
        scheduler.run_now(args.run_now, args.mode)
        return
    
    # Başlat
    scheduler.start(hurricane_mode=not args.classic)


if __name__ == "__main__":
    main()
