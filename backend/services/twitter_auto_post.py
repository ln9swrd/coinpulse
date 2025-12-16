"""
트위터 자동 포스팅 서비스

급등 예측 알림을 트위터에 자동으로 포스팅합니다.
"""
import os
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 트위터 API 설치 필요:
# pip install tweepy
try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    logger.warning("[TwitterBot] tweepy not installed. Run: pip install tweepy")


class TwitterAutoPost:
    """
    트위터 자동 포스팅 클래스

    설정 방법:
    1. https://developer.twitter.com/en/portal/dashboard 접속
    2. 새 앱 생성
    3. API Keys & Tokens 생성
    4. .env 파일에 다음 추가:
       TWITTER_API_KEY=your_api_key
       TWITTER_API_SECRET=your_api_secret
       TWITTER_ACCESS_TOKEN=your_access_token
       TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
       TWITTER_BEARER_TOKEN=your_bearer_token
    """

    def __init__(self):
        if not TWITTER_AVAILABLE:
            raise ImportError("tweepy required. Install: pip install tweepy")

        # API 키 로드
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

        if not all([self.api_key, self.api_secret, self.access_token,
                   self.access_token_secret, self.bearer_token]):
            raise ValueError("Twitter API credentials not found in .env")

        # Twitter API v2 클라이언트 초기화
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )

        logger.info("[TwitterBot] Initialized successfully")

    def post_surge_alert(self, candidate: Dict) -> Optional[str]:
        """
        급등 예측 알림 트윗

        Args:
            candidate: {
                "market": "KRW-XRP",
                "score": 75,
                "current_price": 1250.0
            }

        Returns:
            tweet_id or None
        """
        try:
            market = candidate['market']
            coin_name = market.replace('KRW-', '')
            score = candidate['score']
            price = candidate['current_price']

            # 이모지 선택
            emoji = "🔥" if score >= 70 else "⚡"

            # 해시태그
            hashtags = f"#코인 #{coin_name} #급등예측 #업비트"

            # 트윗 작성
            tweet_text = f"""{emoji} 급등 예측 알림!

코인: #{coin_name}
점수: {score}점
현재가: {price:,.0f}원

백테스트 적중률: 81.25%
평균 수익: +19.12%

👉 실시간 차트 보기
https://coinpulse.sinsi.ai/trading_chart.html?market={market}

{hashtags} #비트코인 #알트코인
"""

            # 트윗 길이 체크 (280자 제한)
            if len(tweet_text) > 280:
                logger.warning(f"[TwitterBot] Tweet too long: {len(tweet_text)} chars")
                # 간단 버전
                tweet_text = f"""{emoji} 급등 예측 {coin_name}

점수: {score}점 | 가격: {price:,.0f}원
백테스트: 81.25% 적중

👉 https://coinpulse.sinsi.ai

{hashtags}"""

            # 트윗 포스팅
            response = self.client.create_tweet(text=tweet_text)
            tweet_id = response.data['id']

            logger.info(f"[TwitterBot] Posted tweet: {tweet_id} for {market}")
            return tweet_id

        except Exception as e:
            logger.error(f"[TwitterBot] Failed to post tweet: {e}")
            return None

    def post_daily_summary(self, stats: Dict) -> Optional[str]:
        """
        일일 요약 트윗

        Args:
            stats: {
                "total_alerts": 5,
                "highest_score": 85,
                "average_score": 72
            }
        """
        try:
            today = datetime.now().strftime('%Y-%m-%d')

            tweet_text = f"""📊 {today} 급등 예측 요약

오늘의 급등 후보: {stats.get('total_alerts', 0)}개
최고 점수: {stats.get('highest_score', 0)}점
평균 점수: {stats.get('average_score', 0)}점

💡 AI 기반 급등 예측 서비스
백테스트 적중률: 81.25%

👉 https://coinpulse.sinsi.ai

#코인투자 #업비트 #급등예측
"""

            response = self.client.create_tweet(text=tweet_text)
            tweet_id = response.data['id']

            logger.info(f"[TwitterBot] Posted daily summary: {tweet_id}")
            return tweet_id

        except Exception as e:
            logger.error(f"[TwitterBot] Failed to post daily summary: {e}")
            return None

    def post_success_story(self, trade: Dict) -> Optional[str]:
        """
        예측 적중 사례 트윗

        Args:
            trade: {
                "market": "KRW-XLM",
                "entry_price": 176.5,
                "exit_price": 218.5,
                "return_pct": 23.8
            }
        """
        try:
            coin_name = trade['market'].replace('KRW-', '')
            return_pct = trade['return_pct']

            tweet_text = f"""✅ 급등 예측 적중!

코인: #{coin_name}
진입가: {trade['entry_price']:,.0f}원
매도가: {trade['exit_price']:,.0f}원
수익률: +{return_pct:.1f}% 🎯

AI 알고리즘이 정확히 예측했습니다!

👉 무료 알림 받기
https://t.me/coinpulse_surge_sinsi_bot

#코인 #업비트 #급등 #{coin_name}
"""

            response = self.client.create_tweet(text=tweet_text)
            tweet_id = response.data['id']

            logger.info(f"[TwitterBot] Posted success story: {tweet_id}")
            return tweet_id

        except Exception as e:
            logger.error(f"[TwitterBot] Failed to post success story: {e}")
            return None


# 사용 예시
if __name__ == "__main__":
    # 환경 변수 설정 확인
    print("트위터 API 키 확인:")
    print(f"API_KEY: {'✓' if os.getenv('TWITTER_API_KEY') else '✗'}")
    print(f"API_SECRET: {'✓' if os.getenv('TWITTER_API_SECRET') else '✗'}")
    print(f"ACCESS_TOKEN: {'✓' if os.getenv('TWITTER_ACCESS_TOKEN') else '✗'}")
    print(f"ACCESS_TOKEN_SECRET: {'✓' if os.getenv('TWITTER_ACCESS_TOKEN_SECRET') else '✗'}")
    print(f"BEARER_TOKEN: {'✓' if os.getenv('TWITTER_BEARER_TOKEN') else '✗'}")

    if all([os.getenv('TWITTER_API_KEY'), os.getenv('TWITTER_BEARER_TOKEN')]):
        try:
            twitter = TwitterAutoPost()

            # 테스트 트윗
            test_candidate = {
                "market": "KRW-XRP",
                "score": 75,
                "current_price": 1250.5
            }

            tweet_id = twitter.post_surge_alert(test_candidate)
            if tweet_id:
                print(f"✓ 테스트 트윗 성공! ID: {tweet_id}")
            else:
                print("✗ 테스트 트윗 실패")

        except Exception as e:
            print(f"✗ 에러: {e}")
    else:
        print("\n.env 파일에 트위터 API 키를 설정하세요:")
        print("TWITTER_API_KEY=your_api_key")
        print("TWITTER_API_SECRET=your_api_secret")
        print("TWITTER_ACCESS_TOKEN=your_access_token")
        print("TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret")
        print("TWITTER_BEARER_TOKEN=your_bearer_token")
