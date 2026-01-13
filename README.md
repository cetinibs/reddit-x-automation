# 🌀 Reddit → X (Twitter) Hurricane Otomasyon Sistemi

## 📋 Genel Bakış

Bu sistem **Hurricane Notları** stratejisine göre optimize edilmiştir:

- **%90 Engagement**: Büyük hesaplara quote/mention yaparak trustscore aktarımı
- **%10 Orijinal Post**: Reddit'ten viral içerik
- **24 Saat Kuralı**: Sessizlik = negatif boost
- **Duygusal Tetikleyiciler**: Para, statü, beğenilme, kabul görme

## 🏗️ Sistem Mimarisi

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Reddit    │────▶│  Python     │────▶│  OpenAI     │────▶│   X API     │
│   .json API │     │  Scraper    │     │  GPT-4o     │     │   Post      │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Hurricane  │
                    │  Scheduler  │
                    └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Quote   │ │  Reply   │ │ Mention  │
        │  Tweets  │ │  to Big  │ │  Users   │
        └──────────┘ │ Accounts │ └──────────┘
                     └──────────┘
```

## 📁 Dosya Yapısı

```
reddit-x-automation/
├── config.py           # API anahtarları ve Hurricane ayarları
├── reddit_scraper.py   # Reddit veri çekme
├── tweet_generator.py  # AI ile tweet oluşturma (duygusal tetikleyiciler)
├── x_poster.py         # X'e paylaşım
├── x_engagement.py     # 🌀 Hurricane engagement modülü (YENİ)
├── main.py             # Ana orkestrasyon + Hurricane komutları
├── scheduler.py        # Hurricane zamanlama
├── requirements.txt    # Bağımlılıklar
└── .env               # Gizli anahtarlar
```

---

## 🌀 Hurricane Stratejisi

### Ana Prensipler

1. **%90 Quote/Mention**: Sadece içerik paylaşmak yetmez
   - Büyük hesapları quote'la
   - Akıllı reply'lar yaz
   - Mention ile görünürlük kazan

2. **Trustscore Aktarımı**: Büyük hesaplardan güven puanı al
   - HP bar 100 olan hesapları hedefle
   - Quote ve reply ile "juice transfer"

3. **24 Saat Kuralı**: 
   - Son posttan 24 saat geçerse = -%20 negatif boost
   - Minimum her 23 saatte bir aktivite

4. **Dwell Time**: 
   - Tartışma yaratan içerik
   - Okuyucuyu 5+ saniye tutma

### Duygusal Tetikleyiciler

- 💰 **Para**: "Pasif gelir", "para kazanmak"
- 🏆 **Statü**: "Başarı", "prestij"
- ❤️ **Beğenilme**: "Tanınmak", "kabul görmek"
- 🆓 **Özgürlük**: "Bağımsızlık", "kendi işin"

---

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
# Repo'yu klonla
git clone <repo-url>
cd reddit-x-automation

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıklar
pip install -r requirements.txt

# Environment
cp .env.example .env
# .env dosyasını düzenle
```

### 2. Hedef Hesapları Ekle

```bash
# Trustscore aktarımı için büyük hesaplar ekle
python main.py --add-target elonmusk
python main.py --add-target levelsio
python main.py --add-target naval
python main.py --add-target paulg

# Listeyi görüntüle
python main.py --list-targets
```

### 3. Test Et

```bash
# 24 saat kuralı kontrolü
python main.py --check-24h

# İstatistikleri görüntüle
python main.py --stats

# Dry run (tweet atmadan)
python main.py --engage --dry-run

# Gerçek engagement
python main.py --engage --lang tr
```

### 4. Scheduler Başlat

```bash
# Hurricane modunda başlat
python scheduler.py

# Veya Docker ile
docker-compose up -d
```

---

## 📖 Kullanım Örnekleri

### Engagement Modu (Hurricane) - %90

```bash
# Otomatik aksiyon seçimi (quote/reply/mention)
python main.py --engage

# Belirli dil ile
python main.py --engage --lang en

# Dry run
python main.py --engage --dry-run --verbose
```

### Orijinal Post Modu - %10

```bash
# Reddit'ten tweet
python main.py --lang tr

# Thread
python main.py --lang en --thread
```

### Monitoring

```bash
# İstatistikler
python main.py --stats

# 24 saat kuralı kontrolü
python main.py --check-24h

# Zamanlanmış görevler
python scheduler.py --list
```

---

## ⏰ Zamanlama Stratejisi

### Hurricane Zamanlaması

| Zaman (TR) | Aksiyon | Açıklama |
|------------|---------|----------|
| 07:00 | 🌀 Engage | Quote/Reply |
| 09:00 | 🌀 Engage | Quote/Reply |
| 11:00 | 🌀 Engage | Quote/Reply |
| 12:00 | 📝 Tweet | Orijinal post |
| 13:00 | 🌀 Engage | Quote/Reply |
| 15:00 | 🌀 Engage | Quote/Reply |
| 17:00 | 🌀 Engage | Quote/Reply |
| 18:00 | 📝 Tweet | Orijinal post |
| 19:00 | 🌀 Engage | Quote/Reply |
| 21:00 | 🌀 Engage + Tweet | İngilizce |

### 24 Saat Kontrolü

- Her 4 saatte bir otomatik kontrol
- 20+ saat sessizlik = uyarı
- 23+ saat = acil aksiyon

---

## 🎯 Reddit Isınma Süreci

Hurricane stratejisine göre:

1. **1 Ay Manuel Karma Kasma**
   - Spam motorlarına yakalanmamak için
   - Gerçek yorumlar ve paylaşımlar
   - Minimum 1000 karma hedefi

2. **Isınma Modu**
   ```bash
   # .env'de
   IS_WARMUP_MODE=true
   ```

3. **Sonra Otomasyon**
   ```bash
   IS_WARMUP_MODE=false
   ```

---

## 📊 Takip Edilecek Subredditler

```python
SUBREDDITS = [
    # Girişimcilik & SaaS (Yüksek pain point)
    "Entrepreneur",      # 4.8M
    "startups",          # 1.8M
    "SaaS",              # 341K
    "SideProject",       # 430K
    "indiehackers",      # 91K
    "MicroSaas",         # 80K
    
    # Teknoloji & AI
    "programming",       # 6M
    "webdev",            # 2.1M
    "ChatGPT",           # 5M
    "vibecoding",        # 35K
    
    # İş & Verimlilik
    "productivity",      # 4M
    "smallbusiness",     # 2.2M
]
```

---

## ⚙️ Environment Variables

```bash
# Hurricane Stratejisi
QUOTE_MENTION_RATIO=0.9        # %90 engagement
ORIGINAL_POST_RATIO=0.1        # %10 orijinal
MAX_SILENCE_HOURS=23           # 24 saat kuralı
DAILY_QUOTE_TARGET=10          # Günlük hedef
DAILY_MENTION_TARGET=5

# Tweet Ayarları
USE_HASHTAGS=false             # Hashtag kullanma
MAX_DAILY_TWEETS=8

# Isınma Modu
IS_WARMUP_MODE=true
WARMUP_DAYS=30
MIN_KARMA=1000
```

---

## 🐳 Docker Deployment

```bash
# Build
docker build -t reddit-x-automation .

# Run
docker-compose up -d

# Logs
docker-compose logs -f
```

---

## ⚠️ Önemli Notlar

1. **24 Saat Kuralı**: Sessizlik = negatif boost, kesinlikle takip et
2. **Hashtag Kullanma**: Engagement düşürür (Hurricane notları)
3. **Quote > Reply**: Quote tweet daha etkili trustscore için
4. **Tartışma Yarat**: Dwell time artırır, algoritma sever
5. **Isınma Süresi**: Reddit'te 1 ay manuel karma kas

---

## 🆘 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| 24 saat uyarısı | Hemen `--engage` çalıştır |
| Hedef hesap yok | `--add-target` ile ekle |
| Quote çalışmıyor | Tweet ID'yi kontrol et |
| API rate limit | Daily limit'leri düşür |

---

## 📈 Metrikler ve Hedefler

### Günlük Hedefler

- [ ] 10 Quote tweet
- [ ] 5 Reply
- [ ] 2-3 Orijinal post
- [ ] %0.5+ engagement rate
- [ ] 24 saat kuralını koru

### Haftalık Hedefler

- [ ] 50+ toplam engagement
- [ ] 5 yeni hedef hesap ekle
- [ ] Engagement rate takibi

---

## 🔄 Gelecek Geliştirmeler

- [x] Hurricane engagement modülü
- [x] 24 saat kuralı kontrolü
- [x] Duygusal tetikleyiciler
- [x] Quote/Reply/Mention desteği
- [ ] Analytics dashboard
- [ ] A/B test
- [ ] Otomatik hedef hesap keşfi
- [ ] Engagement rate tracking
