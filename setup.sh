#!/bin/bash
# ============================================
# Reddit → X Automation - Kurulum Scripti
# ============================================

set -e

echo "🚀 Reddit → X Automation Kurulumu"
echo "=================================="

# Renk tanımları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonksiyonlar
success() { echo -e "${GREEN}✓ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; exit 1; }

# 1. Python kontrolü
echo -e "\n📦 Python kontrolü..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    success "Python $PYTHON_VERSION bulundu"
else
    error "Python3 bulunamadı! Lütfen Python 3.10+ kurun."
fi

# 2. Virtual environment oluştur
echo -e "\n📦 Virtual environment oluşturuluyor..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Virtual environment oluşturuldu"
else
    warning "Virtual environment zaten mevcut"
fi

# 3. Activate et
source venv/bin/activate
success "Virtual environment aktif"

# 4. Bağımlılıkları yükle
echo -e "\n📦 Bağımlılıklar yükleniyor..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
success "Bağımlılıklar yüklendi"

# 5. Dizinleri oluştur
echo -e "\n📁 Dizinler oluşturuluyor..."
mkdir -p logs cache data
success "Dizinler oluşturuldu"

# 6. .env dosyası kontrolü
echo -e "\n🔐 Yapılandırma kontrolü..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    warning ".env dosyası oluşturuldu - API anahtarlarını düzenlemeyi unutma!"
    echo -e "\n${YELLOW}Şimdi .env dosyasını düzenle:${NC}"
    echo "  nano .env"
else
    success ".env dosyası mevcut"
fi

# 7. Test
echo -e "\n🧪 Sistem testi..."
python3 -c "from config import config; print('Config OK')" && success "Config yüklendi"

# 8. Tamamlandı
echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}✓ Kurulum tamamlandı!${NC}"
echo -e "${GREEN}============================================${NC}"

echo -e "\n📋 Sonraki adımlar:"
echo "1. .env dosyasını düzenle: nano .env"
echo "2. API anahtarlarını ekle"
echo "3. Test et: python main.py --dry-run --lang tr"
echo "4. Cron ekle: crontab -e"

echo -e "\n⏰ Örnek cron satırları:"
echo '0 6 * * * cd /opt/reddit-x-bot && ./venv/bin/python main.py --lang tr'
echo '0 10 * * * cd /opt/reddit-x-bot && ./venv/bin/python main.py --lang tr'
echo '0 14 * * * cd /opt/reddit-x-bot && ./venv/bin/python main.py --lang en'
echo '0 18 * * * cd /opt/reddit-x-bot && ./venv/bin/python main.py --lang en'

echo -e "\n🔧 Veya scheduler kullan:"
echo "python scheduler.py"
