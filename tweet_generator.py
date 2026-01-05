"""
Tweet Generator - Claude AI ile tweet oluşturma
"""
import random
from typing import Optional
from loguru import logger
import anthropic

from config import config
from reddit_scraper import RedditPost


class TweetGenerator:
    """Claude AI kullanarak tweet oluşturan generator"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.anthropic.api_key)
        self.model = config.anthropic.model
    
    def _get_system_prompt(self, language: str) -> str:
        """Sistem prompt'u oluştur"""
        if language == "tr":
            return """Sen viral tweet yazan bir sosyal medya uzmanısın.
            
Görevin: Reddit'teki popüler bir konuyu alıp, X (Twitter) için ilgi çekici bir tweet oluşturmak.

KURALLAR:
1. Tweet 260 karakteri geçmemeli
2. Emoji kullan ama abartma (1-3 emoji)
3. Merak uyandıran bir hook ile başla
4. Değer ver - bilgilendirici veya eğlenceli olsun
5. Engagement için soru veya call-to-action ekle
6. Hashtag kullanma (ayrıca eklenecek)
7. Türkçe yaz, doğal ve akıcı olsun
8. Reddit'ten geldiğini belirtme
9. Kendi içeriğinmiş gibi paylaş

FORMAT:
Sadece tweet metnini yaz, başka bir şey ekleme."""

        else:  # en
            return """You are a viral tweet writer and social media expert.

Your task: Take a popular Reddit topic and create an engaging tweet for X (Twitter).

RULES:
1. Tweet must be under 260 characters
2. Use emojis sparingly (1-3 emojis)
3. Start with a hook that creates curiosity
4. Provide value - informative or entertaining
5. Add a question or call-to-action for engagement
6. Don't use hashtags (will be added separately)
7. Write naturally and conversationally
8. Don't mention it's from Reddit
9. Present as your own insight/content

FORMAT:
Just write the tweet text, nothing else."""

    def _get_user_prompt(self, post: RedditPost, language: str) -> str:
        """Kullanıcı prompt'u oluştur"""
        if language == "tr":
            return f"""Reddit'te popüler olan bu konuyu tweet'e çevir:

Subreddit: r/{post.subreddit}
Başlık: {post.title}
Upvote: {post.score}
Yorum: {post.num_comments}

İçerik özeti (varsa):
{post.selftext[:300] if post.selftext else 'İçerik yok, sadece başlık var.'}

Bu konuyu kendi bakış açınla yorumlayarak viral bir Türkçe tweet yaz."""

        else:  # en
            return f"""Turn this popular Reddit topic into a tweet:

Subreddit: r/{post.subreddit}
Title: {post.title}
Upvotes: {post.score}
Comments: {post.num_comments}

Content summary (if any):
{post.selftext[:300] if post.selftext else 'No content, just the title.'}

Create a viral English tweet with your own perspective on this topic."""

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
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                system=self._get_system_prompt(language),
                messages=[
                    {
                        "role": "user",
                        "content": self._get_user_prompt(post, language)
                    }
                ]
            )
            
            tweet_text = message.content[0].text.strip()
            
            # Tweet uzunluk kontrolü
            if len(tweet_text) > 260:
                logger.warning(f"Tweet too long ({len(tweet_text)} chars), truncating...")
                tweet_text = tweet_text[:257] + "..."
            
            # Hashtag ekle
            hashtags = self._get_hashtags(language)
            
            # Hashtag'lerle birlikte 280 karakteri geçmemeli
            max_hashtag_len = 280 - len(tweet_text) - 2
            hashtag_str = ""
            for tag in hashtags:
                if len(hashtag_str) + len(tag) + 1 <= max_hashtag_len:
                    hashtag_str += f" {tag}"
            
            full_tweet = f"{tweet_text}{hashtag_str}"
            
            logger.info(f"Generated tweet ({len(full_tweet)} chars)")
            return full_tweet
            
        except Exception as e:
            logger.error(f"Error generating tweet: {e}")
            return None
    
    def _get_hashtags(self, language: str, count: int = 3) -> list:
        """Rastgele hashtag seç"""
        if language == "tr":
            tags = config.tweet.hashtags_tr
        else:
            tags = config.tweet.hashtags_en
        
        return random.sample(tags, min(count, len(tags)))
    
    def generate_thread(
        self, 
        post: RedditPost, 
        language: str = "tr",
        tweet_count: int = 5
    ) -> list[str]:
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

KURALLAR:
1. Her tweet 260 karakter altında olmalı
2. İlk tweet hook olmalı ve "🧵" ile başlamalı
3. Son tweet CTA içermeli
4. Her tweet tek başına da anlamlı olmalı
5. Numaralandırma kullan (1/, 2/, vs.)

FORMAT:
Her tweet'i yeni satırda yaz, aralarında boş satır bırak."""

        else:
            thread_prompt = f"""Create a {tweet_count}-tweet thread from this popular Reddit topic:

Subreddit: r/{post.subreddit}
Title: {post.title}
Upvotes: {post.score}

Content:
{post.selftext[:500] if post.selftext else 'No content.'}

RULES:
1. Each tweet under 260 characters
2. First tweet should be a hook starting with "🧵"
3. Last tweet should have a CTA
4. Each tweet should make sense standalone
5. Use numbering (1/, 2/, etc.)

FORMAT:
Write each tweet on a new line, with blank lines between."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": thread_prompt}
                ]
            )
            
            response = message.content[0].text.strip()
            tweets = [t.strip() for t in response.split("\n\n") if t.strip()]
            
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
