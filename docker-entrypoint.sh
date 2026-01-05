#!/bin/bash
# ============================================
# Docker Entry Point
# ============================================

set -e

echo "🤖 Reddit → X Automation Bot"
echo "============================="

# .env kontrolü
if [ ! -f "/app/.env" ]; then
    echo "⚠️  .env dosyası bulunamadı!"
    echo "   Environment variables kullanılacak."
fi

# Mod seçimi
case "$1" in
    scheduler)
        echo "📅 Scheduler modu başlatılıyor..."
        exec python scheduler.py
        ;;
    cron)
        echo "⏰ Cron modu başlatılıyor..."
        # Cron daemon'ı foreground'da başlat
        exec cron -f
        ;;
    tweet)
        # Tek seferlik tweet
        LANG=${2:-tr}
        echo "📝 Tweet atılıyor ($LANG)..."
        exec python main.py --lang "$LANG"
        ;;
    dry-run)
        # Test modu
        LANG=${2:-tr}
        echo "🧪 Test modu ($LANG)..."
        exec python main.py --lang "$LANG" --dry-run
        ;;
    stats)
        echo "📊 İstatistikler..."
        exec python main.py --stats
        ;;
    shell)
        echo "🐚 Shell modu..."
        exec /bin/bash
        ;;
    *)
        echo "Kullanım: docker run <image> [scheduler|cron|tweet|dry-run|stats|shell] [tr|en]"
        echo ""
        echo "Modlar:"
        echo "  scheduler  - APScheduler ile zamanlı çalışma (varsayılan)"
        echo "  cron       - Sistem cron ile çalışma"
        echo "  tweet      - Tek seferlik tweet at"
        echo "  dry-run    - Test modu (tweet atmadan)"
        echo "  stats      - İstatistikleri göster"
        echo "  shell      - Bash shell aç"
        exit 1
        ;;
esac
