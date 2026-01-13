"""
Tweet Generator - Hurricane Notları Stratejisi
Duygusal tetikleyiciler ile viral tweet oluşturma
"""
import random
from typing import Optional, List
from loguru import logger
import openai

from config import config
from reddit_scraper import RedditPost


class TweetGenerator:
    """
    OpenAI kullanarak tweet oluşturan generator
    
    Hurricane Stratejisi:
    - Duygusal tetikleyiciler (Para, Statü, Beğenilme, Kabul Görme)
    - Tartışma yaratan içerik (dwell time artırma)
    - Merak uyandıran hook'lar
    - Hashtag kullanmama (engagement düşürür)
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model
    
    def _get_system_prompt(self, language: str) -> str:
        """Sistem prompt'u oluştur - Hurricane stratejisi ile"""
        if language == "tr":
            return """Sen viral tweet yazan bir sosyal medya uzmanısın.

Görevin: Reddit'teki popüler bir konuyu alıp, X (Twitter) için ilgi çekici bir tweet oluşturmak.

HURRICANE STRATEJİSİ:
1. DUYGUSAL TETİKLEYİCİLER kullan:
   - Para kazanma isteği
   - Statü/prestij arzusu
   - Beğenilme/kabul görme ihtiyacı
   - Özgürlük/bağımsızlık hayali

2. TARTIŞMA YARAT (Dwell Time artırma):
   - Kontroversiyel ama hakaret içermeyen görüşler
   - "Çoğu kişi bunu yanlış anlıyor..." gibi hook'lar
   - Polarize edici sorular

3. HOOK TEKNİKLERİ:
   - Merak uyandır: "Bunu bilmiyorsan..."
   - Kayıp korkusu: "Kaçırdığın fırsat..."
   - Otoriteye itiraz: "Herkes yanlış yapıyor..."

KURALLAR:
1. Tweet 260 karakteri geçmemeli
2. Emoji kullan ama abartma (1-2 emoji)
3. HASHTAG KULLANMA (engagement düşürür)
4. Reddit'ten geldiğini belirtme
5. Kendi içeriğin/görüşünmüş gibi paylaş
6. Türkçe yaz, doğal ve akıcı olsun

FORMAT:
Sadece tweet metnini yaz, başka bir şey ekleme."""

        else:  # en
            return """You are a viral tweet writer and social media expert.

Your task: Take a popular Reddit topic and create an engaging tweet for X (Twitter).

HURRICANE STRATEGY:
1. Use EMOTIONAL TRIGGERS:
   - Desire to make money
   - Status/prestige aspiration
   - Need for recognition/acceptance
   - Freedom/independence dreams

2. CREATE DISCUSSION (Increase Dwell Time):
   - Controversial but respectful opinions
   - Hooks like "Most people get this wrong..."
   - Polarizing questions

3. HOOK TECHNIQUES:
   - Create curiosity: "If you don't know this..."
   - Fear of missing out: "The opportunity you're missing..."
   - Challenge authority: "Everyone is doing it wrong..."

RULES:
1. Tweet must be under 260 characters
2. Use emojis sparingly (1-2 emojis)
3. DO NOT use hashtags (decreases engagement)
4. Don't mention it's from Reddit
5. Present as your own insight/content
6. Write naturally and conversationally

FORMAT:
Just write the tweet text, nothing else."""

    def _get_user_prompt(self, post: RedditPost, language: str) -> str:
        """Kullanıcı prompt'u oluştur"""
        if language == "tr":
            return f"""Reddit'te popüler olan bu konuyu viral bir tweet'e çevir:

Subreddit: r/{post.subreddit}
Başlık: {post.title}
Upvote: {post.score}
Yorum: {post.num_comments}

İçerik özeti (varsa):
{post.selftext[:300] if post.selftext else 'İçerik yok, sadece başlık var.'}

Duygusal tetikleyicileri kullanarak ve tartışma yaratarak viral bir Türkçe tweet yaz.
Hedef: Okuyucunun tweet üzerinde 5+ saniye durmasını sağla."""

        else:  # en
            return f"""Turn this popular Reddit topic into a viral tweet:

Subreddit: r/{post.subreddit}
Title: {post.title}
Upvotes: {post.score}
Comments: {post.num_comments}

Content summary (if any):
{post.selftext[:300] if post.selftext else 'No content, just the title.'}

Create a viral English tweet using emotional triggers and creating discussion.
Goal: Make readers spend 5+ seconds on the tweet."""

    def generate_tweet(
        self, 
        post: RedditPost, 
        language: str = "tr"
    ) -> Optional[str]:
        """
        Reddit postundan tweet oluştur
        
        Args:
            post: Reddit post
            language: 'tr' veya 'en'
            
        Returns:
            Tweet metni veya None
        """
        try:
            logger.info(f"Generating {language.upper()} tweet for: {post.title[:50]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(language)
                    },
                    {
                        "role": "user",
                        "content": self._get_user_prompt(post, language)
                    }
                ]
            )
            
            tweet_text = response.choices[0].message.content.strip()
            
            # Tweet uzunluk kontrolü
            if len(tweet_text) > 260:
                logger.warning(f"Tweet too long ({len(tweet_text)} chars), truncating...")
                tweet_text = tweet_text[:257] + "..."
            
            # Hurricane: Hashtag kullanma (varsayılan kapalı)
            if config.tweet.use_hashtags:
                hashtags = self._get_hashtags(language)
                max_hashtag_len = 280 - len(tweet_text) - 2
                hashtag_str = ""
                for tag in hashtags:
                    if len(hashtag_str) + len(tag) + 1 <= max_hashtag_len:
                        hashtag_str += f" {tag}"
                
                tweet_text = f"{tweet_text}{hashtag_str}"
            
            logger.info(f"Generated tweet ({len(tweet_text)} chars)")
            return tweet_text
            
        except Exception as e:
            logger.error(f"Error generating tweet: {e}")
            return None
    
    def _get_hashtags(self, language: str, count: int = 2) -> list:
        """Rastgele hashtag seç (opsiyonel kullanım)"""
        if language == "tr":
            tags = config.tweet.hashtags_tr
        else:
            tags = config.tweet.hashtags_en
        
        return random.sample(tags, min(count, len(tags)))
    
    def generate_quote_comment(
        self,
        original_tweet: str,
        language: str = "tr"
    ) -> Optional[str]:
        """
        Quote tweet için yorum oluştur
        
        Hurricane: Büyük hesapları quote'larken akıllı yorum
        
        Args:
            original_tweet: Alıntılanacak tweet metni
            language: 'tr' veya 'en'
            
        Returns:
            Quote yorumu veya None
        """
        if language == "tr":
            prompt = f"""Aşağıdaki tweet'i quote (alıntı) yapıyorsun. Uygun bir yorum yaz.

Orijinal tweet: "{original_tweet}"

KURALLAR:
1. Maksimum 200 karakter
2. Katma değer ekle - sadece "harika" gibi boş övgüler değil
3. Kendi perspektifini ekle
4. Tartışma başlatabilecek bir açı bul
5. Emoji kullanabilirsin (1-2)
6. Hashtag KULLANMA

Sadece yorum metnini yaz:"""
        else:
            prompt = f"""You're quoting the following tweet. Write an appropriate comment.

Original tweet: "{original_tweet}"

RULES:
1. Maximum 200 characters
2. Add value - not empty praise like "great"
3. Add your perspective
4. Find an angle that could start a discussion
5. You can use emojis (1-2)
6. DO NOT use hashtags

Write only the comment text:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            
            comment = response.choices[0].message.content.strip()
            
            if len(comment) > 200:
                comment = comment[:197] + "..."
            
            return comment
            
        except Exception as e:
            logger.error(f"Error generating quote comment: {e}")
            return None
    
    def generate_reply(
        self,
        original_tweet: str,
        language: str = "tr"
    ) -> Optional[str]:
        """
        Tweet'e reply oluştur
        
        Args:
            original_tweet: Yanıtlanacak tweet metni
            language: 'tr' veya 'en'
            
        Returns:
            Reply metni veya None
        """
        if language == "tr":
            prompt = f"""Aşağıdaki tweet'e yanıt yazıyorsun. Akıllı ve değer katan bir yanıt yaz.

Tweet: "{original_tweet}"

KURALLAR:
1. Maksimum 240 karakter
2. Soru sor veya farklı bir perspektif sun
3. Tartışma başlat ama saygılı ol
4. Generic yanıtlar verme ("katılıyorum" gibi)
5. Bilgi veya deneyim paylaş
6. Emoji kullanabilirsin (1-2)

Sadece yanıt metnini yaz:"""
        else:
            prompt = f"""You're replying to the following tweet. Write a smart, value-adding reply.

Tweet: "{original_tweet}"

RULES:
1. Maximum 240 characters
2. Ask a question or offer a different perspective
3. Start a discussion but be respectful
4. Don't give generic replies ("I agree" etc.)
5. Share information or experience
6. You can use emojis (1-2)

Write only the reply text:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            reply = response.choices[0].message.content.strip()
            
            if len(reply) > 240:
                reply = reply[:237] + "..."
            
            return reply
            
        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            return None
    
    def generate_thread(
        self, 
        post: RedditPost, 
        language: str = "tr",
        tweet_count: int = 5
    ) -> List[str]:
        """
        Reddit postundan thread oluştur
        
        Args:
            post: Reddit post
            language: 'tr' veya 'en'
            tweet_count: Thread'deki tweet sayısı
            
        Returns:
            Tweet listesi
        """
        if language == "tr":
            thread_prompt = f"""Reddit'te popüler olan bu konudan {tweet_count} tweet'lik bir thread oluştur:

Subreddit: r/{post.subreddit}
Başlık: {post.title}
Upvote: {post.score}

İçerik:
{post.selftext[:500] if post.selftext else 'İçerik yok.'}

HURRICANE STRATEJİSİ:
1. İlk tweet MERAK UYANDIRMALI - "Bu konuda çoğu kişi yanılıyor 🧵"
2. Her tweet'te bir duygusal tetikleyici kullan
3. Son tweet CTA içermeli (soru sor veya save/RT iste)
4. Tartışma yaratabilecek açılar bul

KURALLAR:
1. Her tweet 260 karakter altında olmalı
2. İlk tweet "🧵" ile başlamalı
3. Numaralandırma kullan (1/, 2/, vs.)
4. HASHTAG KULLANMA

FORMAT:
Her tweet'i yeni satırda yaz, aralarında boş satır bırak."""

        else:
            thread_prompt = f"""Create a {tweet_count}-tweet thread from this popular Reddit topic:

Subreddit: r/{post.subreddit}
Title: {post.title}
Upvotes: {post.score}

Content:
{post.selftext[:500] if post.selftext else 'No content.'}

HURRICANE STRATEGY:
1. First tweet must CREATE CURIOSITY - "Most people get this wrong 🧵"
2. Use an emotional trigger in each tweet
3. Last tweet should have a CTA (ask a question or request save/RT)
4. Find angles that could create discussion

RULES:
1. Each tweet under 260 characters
2. First tweet should start with "🧵"
3. Use numbering (1/, 2/, etc.)
4. DO NOT use hashtags

FORMAT:
Write each tweet on a new line, with blank lines between."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": thread_prompt}
                ]
            )
            
            text = response.choices[0].message.content.strip()
            tweets = [t.strip() for t in text.split("\n\n") if t.strip()]
            
            logger.info(f"Generated thread with {len(tweets)} tweets")
            return tweets[:tweet_count]
            
        except Exception as e:
            logger.error(f"Error generating thread: {e}")
            return []


# Test için
if __name__ == "__main__":
    from loguru import logger
    import sys
    
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    # Mock post
    test_post = RedditPost(
        id="test123",
        title="I built a SaaS that makes $10k/month in 6 months - here's what I learned",
        subreddit="SaaS",
        score=1500,
        num_comments=234,
        url="https://reddit.com/r/SaaS/test",
        selftext="Started with an idea, validated on Reddit, built MVP in 2 weeks...",
        created_utc=1704067200,
        permalink="/r/SaaS/comments/test123/i_built_a_saas/"
    )
    
    generator = TweetGenerator()
    
    # Türkçe tweet
    print("\n=== Türkçe Tweet ===")
    tr_tweet = generator.generate_tweet(test_post, "tr")
    if tr_tweet:
        print(tr_tweet)
        print(f"({len(tr_tweet)} karakter)")
    
    # İngilizce tweet
    print("\n=== English Tweet ===")
    en_tweet = generator.generate_tweet(test_post, "en")
    if en_tweet:
        print(en_tweet)
        print(f"({len(en_tweet)} characters)")
    
    # Quote yorum
    print("\n=== Quote Comment ===")
    comment = generator.generate_quote_comment("Just launched my startup after 2 years of work!", "en")
    if comment:
        print(comment)
