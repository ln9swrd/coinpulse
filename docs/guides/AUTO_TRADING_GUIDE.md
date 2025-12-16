# 🤖 CoinPulse Auto Trading Guide

## 정책 기반 자동매매 시스템 사용 가이드

생성일: 2025-10-26
업데이트: 2025-10-26

---

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [빠른 시작](#빠른-시작)
3. [정책 관리 UI 사용법](#정책-관리-ui-사용법)
4. [정책 설정 가이드](#정책-설정-가이드)
5. [시뮬레이션 모드](#시뮬레이션-모드)
6. [주의사항 및 리스크](#주의사항-및-리스크)

---

## 1. 시스템 개요

### 1.1 주요 기능

✅ **정책 기반 자동매매**
- 코인별 맞춤 정책 설정
- 전략 선택 (추세 추종, 모멘텀, 평균 회귀)
- 손절매/익절매 자동 실행

✅ **실시간 모니터링**
- 거래 로그 실시간 표시
- 자동매매 상태 확인
- 정책 활성화/비활성화 토글

✅ **리스크 관리**
- 포지션 크기 제한
- 손절매 임계값 설정
- 익절매 목표 설정

### 1.2 아키텍처

```
Frontend (policy_manager.html)
    ↓
    ├─ 정책 설정 UI
    ├─ 실시간 모니터링
    └─ 로그 표시

Backend (simple_dual_server.py:8081)
    ↓
    ├─ AutoTradingEngine
    ├─ 정책 관리 (trading_policies.json)
    ├─ 시장 분석 (SMA, RSI)
    └─ 자동매매 스케줄러
```

---

## 2. 빠른 시작

### 2.1 서버 시작

#### Option A: 빠른 시작 (권장)
```bash
# 탐색기에서 더블클릭
QUICK_START.bat
```

#### Option B: 수동 시작
```bash
# CMD에서 실행
python clean_upbit_server.py    # 포트 8080
python simple_dual_server.py    # 포트 8081
```

### 2.2 정책 관리 UI 열기

브라우저에서 접속:
```
http://localhost:8080/frontend/policy_manager.html
```

### 2.3 첫 정책 생성

1. "Add New Coin Policy" 버튼 클릭
2. 코인 심볼 입력 (예: KRW-BTC)
3. 정책 설정 입력
4. "Save Policy" 클릭

---

## 3. 정책 관리 UI 사용법

### 3.1 화면 구성

#### Header
- **Auto Trading Status**: 전체 자동매매 활성화 상태
- **Active/Inactive Badge**: 현재 상태 표시

#### Global Settings
- **Auto Trading Toggle**: 전체 활성화/비활성화
- **Check Interval**: 자동매매 체크 주기 (초)
- **Max Position Size**: 최대 포지션 크기 (%)
- **Risk Level**: 리스크 레벨 (Low/Medium/High)

#### Coin Policies
- **정책 카드**: 코인별 정책 설정 표시
- **Toggle Switch**: 개별 코인 활성화/비활성화
- **Edit Button**: 정책 수정
- **Delete Button**: 정책 삭제

#### Trading Logs
- **실시간 로그**: 매매 활동 실시간 표시
- **색상 구분**:
  - 🟢 Green: 매수 (BUY)
  - 🔴 Red: 매도 (SELL)
  - 🔵 Blue: 정보 (INFO)

### 3.2 주요 기능

#### 자동매매 활성화
```
1. Global Settings에서 "Auto Trading" 토글 클릭
2. 상태가 "Active"로 변경되면 성공
3. 설정된 간격(기본 60초)마다 자동 실행
```

#### 정책 추가
```
1. "Add New Coin Policy" 버튼 클릭
2. 모달에서 정책 입력:
   - Coin Symbol: KRW-BTC, KRW-ETH 등
   - Strategy: 전략 선택
   - Timeframe: 시간 프레임
   - Buy/Sell Threshold: 매수/매도 임계값
   - Stop Loss: 손절매 비율
   - Take Profit: 익절매 목표
   - Position Size: 포지션 크기
3. "Save Policy" 클릭
```

#### 정책 수정
```
1. 정책 카드에서 "✏️" 버튼 클릭
2. 모달에서 값 수정
3. "Save Policy" 클릭
```

#### 정책 삭제
```
1. 정책 카드에서 "🗑️" 버튼 클릭
2. 확인 다이얼로그에서 "확인" 클릭
```

#### 수동 사이클 실행
```
1. "▶️ Run One Cycle" 버튼 클릭
2. 로그에서 실행 결과 확인
```

---

## 4. 정책 설정 가이드

### 4.1 정책 파라미터 설명

#### Coin Symbol
- 형식: `KRW-{코인심볼}`
- 예시: `KRW-BTC`, `KRW-ETH`, `KRW-XRP`

#### Strategy (전략)
- **Trend Following** (추세 추종)
  - 추세를 따라가는 전략
  - 이동평균선 기반
  - 장기 투자에 적합

- **Momentum** (모멘텀)
  - 가격 변동성 활용
  - RSI 지표 활용
  - 단기 투자에 적합

- **Mean Reversion** (평균 회귀)
  - 평균으로 회귀하는 성질 활용
  - 과매수/과매도 구간 활용
  - 박스권 장세에 적합

#### Timeframe (시간 프레임)
- `1m`: 1분봉 (초단타)
- `5m`: 5분봉 (단타)
- `15m`: 15분봉 (단기)
- `1h`: 1시간봉 (중기, 권장)
- `4h`: 4시간봉 (중장기)
- `1d`: 일봉 (장기)

#### Buy Threshold (매수 임계값, %)
- 매수 신호 발생 임계값
- 예: 2% = 신호 강도 2% 이상일 때 매수
- 권장: 1-5%

#### Sell Threshold (매도 임계값, %)
- 매도 신호 발생 임계값
- 예: 5% = 신호 강도 5% 이상일 때 매도
- 권장: 3-10%

#### Stop Loss (손절매, %)
- 최대 손실 허용 비율
- 예: 3% = 매수가 대비 3% 하락 시 자동 손절
- 권장: 2-5%

#### Take Profit (익절매, %)
- 목표 수익률
- 예: 10% = 매수가 대비 10% 상승 시 자동 익절
- 권장: 5-15%

#### Position Size (포지션 크기, %)
- 전체 자산 대비 투자 비율
- 예: 5% = 보유 자산의 5%만 투자
- 권장: 3-10%

### 4.2 추천 정책 설정

#### 보수적 (저위험)
```json
{
  "strategy": "trend_following",
  "timeframe": "1h",
  "buy_threshold": 1.0,
  "sell_threshold": 3.0,
  "stop_loss": 2.0,
  "take_profit": 5.0,
  "position_size": 3.0
}
```

#### 균형적 (중위험)
```json
{
  "strategy": "momentum",
  "timeframe": "1h",
  "buy_threshold": 2.0,
  "sell_threshold": 5.0,
  "stop_loss": 3.0,
  "take_profit": 10.0,
  "position_size": 5.0
}
```

#### 공격적 (고위험)
```json
{
  "strategy": "momentum",
  "timeframe": "15m",
  "buy_threshold": 3.0,
  "sell_threshold": 8.0,
  "stop_loss": 5.0,
  "take_profit": 15.0,
  "position_size": 10.0
}
```

### 4.3 코인별 추천 설정

#### 비트코인 (KRW-BTC)
- 변동성이 상대적으로 낮음
- 추세 추종 전략 권장
- Position Size: 5-10%

#### 이더리움 (KRW-ETH)
- 비트코인과 유사한 패턴
- 추세 추종 또는 모멘텀
- Position Size: 3-7%

#### 알트코인 (KRW-XRP, KRW-ADA 등)
- 변동성이 높음
- 손절매 비율 낮게 설정 (2-3%)
- Position Size: 2-5%

---

## 5. 시뮬레이션 모드

### 5.1 현재 상태

⚠️ **현재는 시뮬레이션 모드로만 작동합니다**

- 실제 주문 API는 연결되지 않음
- 매매 신호만 로그에 기록됨
- 실제 거래는 실행되지 않음

### 5.2 테스트 방법

1. **정책 설정**
   ```
   - 테스트용 정책 추가 (KRW-BTC)
   - 낮은 임계값 설정 (신호 발생 확률 높임)
   ```

2. **자동매매 활성화**
   ```
   - Auto Trading Toggle 켜기
   - Check Interval: 60초로 설정
   ```

3. **수동 사이클 실행**
   ```
   - "Run One Cycle" 버튼 클릭
   - 로그에서 신호 확인
   ```

4. **로그 확인**
   ```
   - Trading Logs 섹션 확인
   - BUY/SELL 신호 발생 여부 확인
   ```

### 5.3 예상 로그 출력

```
[2025-10-26 10:30:15] INFO KRW-BTC - Analyzing market condition
[2025-10-26 10:30:16] BUY KRW-BTC @ 45,000,000 KRW - Signal strength: 2.5%
[2025-10-26 10:35:20] INFO KRW-ETH - Analyzing market condition
[2025-10-26 10:35:21] SELL KRW-ETH @ 3,200,000 KRW - Take profit triggered
```

---

## 6. 주의사항 및 리스크

### 6.1 ⚠️ 중요 경고

#### 실제 주문 기능 미구현
```
현재 버전은 시뮬레이션 모드만 지원합니다.
실제 주문 API는 Phase 2에서 구현될 예정입니다.
```

#### 투자 리스크
```
- 자동매매는 손실 가능성이 있습니다
- 소액으로 시작하여 점진적으로 확대하세요
- 항상 손절매를 설정하세요
- 전체 자산의 10% 이상 투자하지 마세요
```

#### 기술적 리스크
```
- 네트워크 장애 가능성
- API 호출 제한
- 서버 다운타임
- 예상치 못한 버그
```

### 6.2 권장사항

#### 시작 전
- [ ] 정책 설정을 충분히 검토
- [ ] 시뮬레이션 모드로 먼저 테스트
- [ ] 손절매 비율 반드시 설정
- [ ] Position Size를 작게 시작 (3-5%)

#### 운영 중
- [ ] 정기적으로 로그 확인
- [ ] 시장 상황 변화 모니터링
- [ ] 정책 성과 분석
- [ ] 필요시 정책 조정

#### 위험 신호
- 🚨 연속 3회 이상 손절매 발생
- 🚨 일일 손실 5% 초과
- 🚨 예상과 다른 거래 패턴
- 🚨 시스템 에러 반복 발생

→ **즉시 자동매매 중지하고 점검**

### 6.3 지원 및 문의

#### 문제 발생 시
1. Trading Logs에서 에러 메시지 확인
2. 브라우저 콘솔 (F12) 에러 확인
3. 서버 로그 확인
4. GitHub Issues에 문의

#### 업데이트 확인
- GitHub Repository 확인
- CHANGELOG.md 참고
- 정기적으로 Pull

---

## 7. 다음 단계 (Roadmap)

### Phase 2: 실제 주문 연동 (예정)
- [ ] Upbit 주문 API 연동
- [ ] 주문 체결 확인
- [ ] 잔고 실시간 업데이트
- [ ] 거래 수수료 반영

### Phase 3: 고급 기능 (예정)
- [ ] 백테스트 기능 완성
- [ ] 고급 지표 추가 (MACD, Bollinger Bands)
- [ ] 알림 시스템 (Telegram, Email)
- [ ] 성과 분석 대시보드

---

## 8. FAQ

### Q1: 자동매매가 작동하지 않아요
```
A: 다음을 확인하세요:
1. Auto Trading Toggle이 켜져 있는지
2. 개별 정책도 활성화되어 있는지
3. 서버가 정상 실행 중인지 (포트 8081)
4. 브라우저 콘솔에 에러가 없는지
```

### Q2: 정책을 저장했는데 반영이 안 돼요
```
A: 다음을 시도하세요:
1. "Refresh" 버튼 클릭
2. 페이지 새로고침 (F5)
3. 브라우저 캐시 삭제 (Ctrl+F5)
4. trading_policies.json 파일 직접 확인
```

### Q3: 로그가 표시되지 않아요
```
A: 다음을 확인하세요:
1. "Run One Cycle" 버튼으로 수동 실행
2. 정책 조건이 너무 까다롭지 않은지
3. 시장 데이터가 정상적으로 로드되는지
4. 네트워크 연결 상태
```

### Q4: 실제 돈으로 거래되나요?
```
A: 아니오! 현재 버전은 시뮬레이션만 지원합니다.
실제 주문 기능은 Phase 2에서 추가될 예정입니다.
```

### Q5: 정책을 여러 개 동시에 실행할 수 있나요?
```
A: 네! 여러 코인에 대해 각각 다른 정책을 설정하고
동시에 실행할 수 있습니다.
```

---

## 9. 참고 자료

### 관련 문서
- `AUTO_TRADING_REVIEW.md` - 시스템 상세 분석
- `CLAUDE.md` - 프로젝트 전체 지침
- `trading_policies.json` - 정책 파일

### 관련 파일
- `frontend/policy_manager.html` - UI
- `frontend/js/policy_manager.js` - 컨트롤러
- `simple_dual_server.py` - 백엔드 API

### Upbit API 문서
- https://docs.upbit.com/reference/

---

**문서 버전**: 1.0
**작성일**: 2025-10-26
**업데이트**: 2025-10-26
**작성자**: Claude Code Assistant
