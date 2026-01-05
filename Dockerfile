# ============================================
# Reddit → X Automation - Dockerfile
# Coolify / Docker deployment için
# ============================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="Reddit X Bot"
LABEL description="Reddit to X/Twitter automation bot"

# Timezone ayarı
ENV TZ=Europe/Istanbul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Çalışma dizini
WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY . .

# Dizinleri oluştur
RUN mkdir -p logs cache data

# Cron dosyası oluştur
RUN echo "# Reddit X Bot Cron Jobs" > /etc/cron.d/reddit-x-bot \
    && echo "0 6 * * * root cd /app && python main.py --lang tr >> /app/logs/cron.log 2>&1" >> /etc/cron.d/reddit-x-bot \
    && echo "0 10 * * * root cd /app && python main.py --lang tr >> /app/logs/cron.log 2>&1" >> /etc/cron.d/reddit-x-bot \
    && echo "0 14 * * * root cd /app && python main.py --lang en >> /app/logs/cron.log 2>&1" >> /etc/cron.d/reddit-x-bot \
    && echo "0 18 * * * root cd /app && python main.py --lang en >> /app/logs/cron.log 2>&1" >> /etc/cron.d/reddit-x-bot \
    && echo "" >> /etc/cron.d/reddit-x-bot \
    && chmod 0644 /etc/cron.d/reddit-x-bot \
    && crontab /etc/cron.d/reddit-x-bot

# Çalıştırma scripti
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Volume'lar
VOLUME ["/app/logs", "/app/cache", "/app/data"]

# Entry point
ENTRYPOINT ["/docker-entrypoint.sh"]

# Varsayılan komut: scheduler
CMD ["scheduler"]
