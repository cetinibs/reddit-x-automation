# 🤖 Reddit → X (Twitter) AI Otomasyon Sistemi

## 📋 Genel Bakış

Bu sistem:
- Reddit'teki popüler konuları otomatik tarar
- AI ile Türkçe ve İngilizce tweet'ler oluşturur
- Belirlenen saatlerde X'te paylaşır
- Tamamen otomatik çalışır

## 🏗️ Sistem Mimarisi

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Reddit    │────▶│  Python     │────▶│  Claude/    │────▶│   X API     │
│   .json API │     │  Scraper    │     │  OpenAI     │     │   Post      │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Cron      │
                    │   Scheduler │
                    └─────────────┘
```

## 📁 Dosya Yapısı

```
reddit-x-automation/
├── config.py           # API anahtarları ve ayarlar
├── reddit_scraper.py   # Reddit veri çekme
├── tweet_generator.py  # AI ile tweet oluşturma
├── x_poster.py         # X'e paylaşım
├── main.py             # Ana orkestrasyon
├── scheduler.py        # Zamanlama
├── requirements.txt    # Bağımlılıklar
└── .env               # Gizli anahtarlar
```

---

## 🚀 ADIM 1: Gereksinimler

### 1.1 Sunucu Gereksinimleri
- Python 3.10+
- Hetzner Cloud (senin mevcut altyapın) ✅
- Coolify veya Docker ✅

### 1.2 API Anahtarları (Ücretsiz/Düşük Maliyetli)

| Servis | Amaç | Maliyet |
|--------|------|---------|
| Reddit | Veri çekme | Ücretsiz (.json endpoint) |
| Anthropic Claude | Tweet oluşturma | $5 kredi ile başla |
| X Developer | Tweet paylaşma | Ücretsiz (Basic tier) |

---

## 🔧 ADIM 2: X Developer Hesabı Kurulumu

### 2.1 Developer Portal'a Kaydol
1. https://developer.twitter.com adresine git
2. "Sign up for Free Account" tıkla
3. Use case olarak "Making a bot" seç

### 2.2 App Oluştur
1. Developer Portal → Projects & Apps → Create App
2. App ismi: "Reddit Trends Bot" (veya istediğin)
3. App permissions: **Read and Write** seç

### 2.3 API Anahtarlarını Al
```
API Key: xxxxxxxxxxxxxx
API Secret: xxxxxxxxxxxxxx
Access Token: xxxxxxxxxxxxxx
Access Token Secret: xxxxxxxxxxxxxx
Bearer Token: xxxxxxxxxxxxxx
```

⚠️ **ÖNEMLİ**: Bu anahtarları güvenli sakla!

---

## 🔧 ADIM 3: Claude API Kurulumu

### 3.1 Anthropic Console
1. https://console.anthropic.com adresine git
2. API Keys → Create Key
3. Anahtarı kopyala

### 3.2 Kredi Yükleme
- İlk $5 yeterli (binlerce tweet için)
- Pay as you go model

---

## 🔧 ADIM 4: Sunucu Kurulumu

### 4.1 Coolify'da Yeni Servis Oluştur

```bash
# SSH ile sunucuya bağlan
ssh root@your-hetzner-ip

# Proje klasörü oluştur
mkdir -p /opt/reddit-x-bot
cd /opt/reddit-x-bot
```

### 4.2 Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

---

## 📝 ADIM 5: Kod Dosyalarını Oluştur

Aşağıdaki dosyaları sırayla oluştur:

### Dosya Listesi:
1. `requirements.txt` - Bağımlılıklar
2. `.env` - Gizli anahtarlar
3. `config.py` - Yapılandırma
4. `reddit_scraper.py` - Reddit tarama
5. `tweet_generator.py` - AI tweet oluşturma
6. `x_poster.py` - X paylaşım
7. `main.py` - Ana program
8. `scheduler.py` - Zamanlayıcı

---

## ⏰ ADIM 6: Zamanlama Ayarları

### Önerilen Paylaşım Saatleri

| Saat (TR) | Saat (UTC) | Dil | Hedef Kitle |
|-----------|------------|-----|-------------|
| 09:00 | 06:00 | 🇹🇷 Türkçe | Türkiye sabah |
| 13:00 | 10:00 | 🇹🇷 Türkçe | Türkiye öğle |
| 17:00 | 14:00 | 🇬🇧 İngilizce | US sabah |
| 21:00 | 18:00 | 🇬🇧 İngilizce | US öğle |

### Cron Ayarları

```bash
# Crontab düzenle
crontab -e

# Şu satırları ekle:
0 6 * * * /opt/reddit-x-bot/venv/bin/python /opt/reddit-x-bot/main.py --lang tr
0 10 * * * /opt/reddit-x-bot/venv/bin/python /opt/reddit-x-bot/main.py --lang tr
0 14 * * * /opt/reddit-x-bot/venv/bin/python /opt/reddit-x-bot/main.py --lang en
0 18 * * * /opt/reddit-x-bot/venv/bin/python /opt/reddit-x-bot/main.py --lang en
```

---

## 🎯 ADIM 7: Test ve Başlatma

### 7.1 Manuel Test

```bash
cd /opt/reddit-x-bot
source venv/bin/activate

# Sadece Reddit tarama testi
python reddit_scraper.py

# Sadece tweet oluşturma testi
python tweet_generator.py

# Tam test (tweet atmadan)
python main.py --dry-run --lang tr

# Gerçek paylaşım
python main.py --lang tr
```

### 7.2 Log Takibi

```bash
# Logları izle
tail -f /opt/reddit-x-bot/logs/bot.log
```

---

## 📊 Takip Edilecek Subredditler

```python
SUBREDDITS = [
    # Girişimcilik
    "Entrepreneur",      # 4.8M
    "startups",          # 1.8M
    "SaaS",              # 341K
    "SideProject",       # 430K
    "indiehackers",      # 91K
    "MicroSaas",         # 80K
    
    # Teknoloji & AI
    "programming",       # 6M
    "webdev",            # 2.1M
    "artificial",        # 1.5M
    "ChatGPT",           # 5M
    "vibecoding",        # 35K
    
    # İş & Verimlilik
    "productivity",      # 4M
    "smallbusiness",     # 2.2M
    "Business_Ideas",    # 359K
]
```

---

## 🔄 Tweet Formatları

### Türkçe Format
```
🔥 Reddit'te trend: [KONU]

[AI tarafından oluşturulan içerik]

#girişimcilik #teknoloji #trend
```

### İngilizce Format
```
🔥 Trending on Reddit: [TOPIC]

[AI generated content]

#startup #tech #trending
```

---

## ⚠️ Önemli Notlar

1. **Rate Limiting**: X API günde 50 tweet sınırı (Free tier)
2. **Reddit ToS**: Aşırı scraping yapma, cache kullan
3. **AI Maliyeti**: Claude Haiku daha ucuz, Sonnet daha kaliteli
4. **Spam Önleme**: Aynı içeriği tekrar paylaşma

---

## 🆘 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| X API 403 | App permissions kontrol et |
| Reddit 429 | Rate limit, 60sn bekle |
| Claude timeout | Retry logic ekle |
| Tweet duplicate | Hash kontrolü ekle |

---

## 📈 Gelecek Geliştirmeler

- [ ] Analytics dashboard
- [ ] A/B test için farklı formatlar
- [ ] Engagement takibi
- [ ] Otomatik hashtag önerisi
- [ ] Thread desteği
