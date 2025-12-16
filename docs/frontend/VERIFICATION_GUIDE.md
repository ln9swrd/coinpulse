# 🔍 CoinPulse 기능 검증 가이드

## 📋 목차
1. [개요](#개요)
2. [검증 도구 사용법](#검증-도구-사용법)
3. [수동 검증 방법](#수동-검증-방법)
4. [기능별 상세 체크리스트](#기능별-상세-체크리스트)
5. [알려진 이슈](#알려진-이슈)
6. [문제 해결](#문제-해결)

---

## 개요

CoinPulse 트레이딩 차트의 모든 UI 기능을 체계적으로 검증하기 위한 가이드입니다.

### 검증 범위
- **총 기능 수**: 60개 이상
- **주요 카테고리**: 9개
- **우선순위**: High/Medium/Low

### 검증 방법
1. **자동 검증**: `verify_features.html` 사용
2. **수동 검증**: 브라우저에서 직접 테스트
3. **콘솔 검증**: 개발자 도구로 로그 확인

---

## 검증 도구 사용법

### 1. 자동 검증 페이지 열기

```bash
# 브라우저에서 접속
http://localhost:8080/frontend/verify_features.html
```

### 2. 전체 테스트 실행

1. **"전체 테스트 실행"** 버튼 클릭
2. 자동으로 trading_chart.html 창이 열림
3. 3초 대기 후 자동 검증 시작
4. 각 기능의 존재 여부 및 동작 가능 여부 확인
5. 결과는 실시간으로 업데이트

### 3. 선택 항목 테스트

1. 검증하고 싶은 기능 체크박스 선택
2. **"선택 항목 테스트"** 버튼 클릭
3. 선택한 기능만 검증

### 4. 리포트 내보내기

1. 테스트 완료 후 **"리포트 내보내기"** 버튼 클릭
2. Markdown 형식의 검증 리포트 다운로드
3. 파일명: `verification_report_YYYY-MM-DD.md`

---

## 수동 검증 방법

### 준비 단계

1. **서버 실행 확인**
   ```bash
   # 차트 서버 (포트 8080)
   python clean_upbit_server.py

   # 거래 서버 (포트 8081)
   python simple_dual_server.py
   ```

2. **브라우저 열기**
   ```
   http://localhost:8080/frontend/trading_chart.html
   ```

3. **개발자 도구 열기** (F12)
   - Console 탭 확인
   - 에러 메시지 체크

---

## 기능별 상세 체크리스트

### ✅ 1. 헤더 섹션 (Header Row)

#### 1.1 포트폴리오 정보
- [ ] **장기 보유 코인 개수** (`#long-term-count`)
  - 숫자 표시 확인
  - 실시간 업데이트 확인

- [ ] **단기 보유 코인 개수** (`#short-term-count`)
  - 숫자 표시 확인

- [ ] **투자 중인 코인** (`#investment-count`)
  - 형식: `0/3` (현재/최대)

- [ ] **예산 금액** (`#budget-amount`)
  - 천 단위 구분자 표시
  - 단위: 원

- [ ] **수익률** (`#profit-rate`)
  - 퍼센트 표시
  - 양수: `+`, 음수: `-`

#### 1.2 자동매매 버튼
- [ ] **보유코인 자동매매** (`#holdings-auto-btn`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭
  2. 상태 변경 확인: "비활성화" ↔ "활성화"
  3. 콘솔 로그 확인
  ```

- [ ] **단기투자 자동매매** (`#active-auto-btn`)
  - 보유코인과 동일한 동작

- [ ] **정책 설정** (`#policy-btn`)
  - 클릭 시 정책 설정 페이지로 이동 또는 모달 열기

---

### ✅ 2. 차트 설정 (Chart Settings)

#### 2.1 시간 프레임
- [ ] **시간 선택** (`#timeframe`)
  ```javascript
  // 테스트 방법
  1. 드롭다운 클릭
  2. "1분", "5분", "15분", "1시간", "4시간", "일봉", "주봉" 선택
  3. 차트 자동 업데이트 확인
  4. 콘솔: "[Working] Timeframe changed to: XXX"
  ```

#### 2.2 코인 선택
- [ ] **코인 검색** (`#coin-search`)
  ```javascript
  // 테스트 방법
  1. 검색창에 "비트", "btc", "KRW-BTC" 입력
  2. 실시간 필터링 확인
  3. 대소문자 구분 없이 작동 확인
  ```

- [ ] **코인 선택** (`#coin-select`)
  ```javascript
  // 테스트 방법
  1. 드롭다운에서 다른 코인 선택
  2. 차트 자동 전환 확인
  3. 가격 정보 업데이트 확인
  ```

- [ ] **코인 목록 새로고침** (`#refresh-coins`)
  - 클릭 시 전체 코인 목록 재로드

---

### ✅ 3. 기술적 지표 (Technical Indicators)

#### 3.1 이평선 설정
- [ ] **이평선 설정 버튼** (`#ma-settings-btn`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭
  2. 모달 열림 확인
  3. MA20, MA50, MA100, MA200, MA300, MA500, MA1000 체크박스 확인
  4. 각 이평선의 색상 표시 확인
  ```

- [ ] **MA 적용**
  ```javascript
  // 테스트 방법
  1. 체크박스 선택
  2. "적용" 버튼 클릭
  3. 차트에 이평선 표시 확인
  4. localStorage에 저장 확인
  ```

#### 3.2 RSI
- [ ] **RSI 토글** (`#rsi-toggle`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭 → active 클래스 추가
  2. RSI 패널 표시 (#rsi-container)
  3. RSI 값 계산 및 차트 렌더링 확인
  4. 다시 클릭 → 패널 숨김
  ```

#### 3.3 MACD
- [ ] **MACD 토글** (`#macd-toggle`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭
  2. MACD 패널 표시 (#macd-container)
  3. MACD Line, Signal Line, Histogram 표시 확인
  ```

#### 3.4 Bollinger Bands
- [ ] **BB 토글** (`#bollinger-toggle`)
  - 메인 차트에 상단/중간/하단 밴드 표시

#### 3.5 SuperTrend
- [ ] **SuperTrend 토글** (`#supertrend-toggle`)
  - 메인 차트에 슈퍼트렌드 선 표시

---

### ✅ 4. 그리기 도구 (Drawing Tools)

#### 4.1 추세선
- [ ] **추세선 그리기** (`#draw-trendline`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭 → active 상태
  2. 차트에서 시작점 클릭
  3. 끝점 클릭
  4. 추세선 생성 확인
  ```

#### 4.2 피보나치
- [ ] **피보나치 되돌림** (`#draw-fibonacci`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭
  2. 시작점 선택 (고점 또는 저점)
  3. 끝점 선택
  4. 23.6%, 38.2%, 50%, 61.8%, 100% 레벨 표시 확인
  ```

#### 4.3 수평선/수직선
- [ ] **수평선** (`#draw-horizontal`)
  - 가격 레벨에 수평선 추가

- [ ] **수직선** (`#draw-vertical`)
  - 시간 레벨에 수직선 추가

#### 4.4 관리
- [ ] **모두 지우기** (`#clear-trendlines`)
  - 모든 그리기 요소 삭제

- [ ] **그리기 목록** (`#show-drawings`)
  - 모달 열기
  - 그리기 목록 표시
  - 개별 삭제 기능

---

### ✅ 5. 차트 액션 (Chart Actions)

#### 5.1 테마
- [ ] **테마 토글** (`#theme-toggle`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭
  2. 다크 ↔ 라이트 테마 전환 확인
  3. localStorage 저장 확인: localStorage.getItem('theme')
  4. 페이지 새로고침 후 테마 유지 확인
  ```

#### 5.2 지지저항선
- [ ] **지지저항선 토글** (`#support-resistance-toggle`)
  ```javascript
  // 테스트 방법 (2025-10-15 수정 완료)
  1. 버튼 클릭 → active 클래스
  2. 콘솔 확인:
     - "[SR] Calculated levels: X"
     - "[SR] Found X levels, merged to Y returning Z"
     - "[SR] Drew support/resistance lines"
  3. 차트에서 확인:
     - 초록색 선 (지지선)
     - 빨간색 선 (저항선)
     - 최대 5개 선 표시
  4. 다시 클릭 → 모든 선 제거
     - 콘솔: "[SR] Removing X support/resistance lines"
  ```

#### 5.3 이평선
- [ ] **이평선 토글** (`#ma-toggle`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭
  2. 모든 이평선 표시/숨김
  3. 설정된 이평선만 토글됨 확인
  ```

#### 5.4 매매마커
- [ ] **매매마커 토글** (`#trade-markers-toggle`)
  ```javascript
  // 테스트 방법
  1. 기본값: active (표시)
  2. 클릭 시 매수/매도 마커 숨김
  3. 다시 클릭 시 마커 표시
  ```

#### 5.5 매매이력
- [ ] **매매이력 버튼** (`#show-history`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭
  2. 모달 열림 (#history-modal)
  3. 매매 내역 표시:
     - 거래 타입 (BUY/SELL)
     - 거래 시간
     - 가격
  4. 새로고침 버튼 동작 확인
  5. 닫기 버튼 동작 확인
  ```

#### 5.6 미체결
- [ ] **미체결 토글** (`#pending-order-toggle`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭
  2. 미체결 주문 마커 표시
  3. 콘솔: "[PENDING] Loading pending orders"
  ```

#### 5.7 거래량
- [ ] **거래량 토글** (`#volume-toggle`)
  ```javascript
  // 테스트 방법
  1. 버튼 클릭
  2. 거래량 차트 표시/숨김
  3. 기본값: 표시
  ```

---

### ✅ 6. 차트 렌더링 (Chart Rendering)

#### 6.1 메인 차트
- [ ] **캔들스틱 차트** (`#chart-container`)
  ```javascript
  // 검증 항목
  1. 캔들 렌더링 (상승: 초록, 하락: 빨강)
  2. 크로스헤어 동작
  3. 마우스 휠로 확대/축소
  4. 드래그로 이동
  5. 더블클릭으로 전체 보기
  ```

- [ ] **거래량 차트**
  ```javascript
  // 검증 항목
  1. 메인 차트 하단에 표시
  2. 색상: 상승(초록), 하락(빨강)
  3. 거래량 값 확인
  ```

#### 6.2 TradingView 방식 로딩
- [ ] **초기 로딩**
  ```javascript
  // 콘솔 확인
  "[Working] Converted 200 initial candles"
  "[Working] Initial data set successfully"
  ```

- [ ] **과거 데이터 로딩**
  ```javascript
  // 테스트 방법
  1. 차트를 왼쪽 끝까지 스크롤
  2. 자동으로 과거 데이터 로드
  3. 콘솔: "[Working] Historical data loaded"
  4. 중복 데이터 없음 확인
  ```

- [ ] **자동 업데이트**
  ```javascript
  // 30초마다 자동 업데이트
  "[Working] Auto update triggered"
  "[Working] Latest data loaded"
  ```

---

### ✅ 7. 보유 코인 패널 (Holdings Panel)

- [ ] **보유 코인 리스트** (`#holdings-list`)
  ```javascript
  // 표시 항목
  1. 코인명 (예: BTC, ETH, XRP)
  2. 평균단가
  3. 수익률 (색상: 양수 초록, 음수 빨강)
  ```

- [ ] **새로고침** (`#refresh-holdings`)
  - 클릭 시 보유 코인 데이터 갱신

- [ ] **코인 클릭**
  ```javascript
  // 테스트 방법
  1. 보유 코인 중 하나 클릭
  2. 해당 코인 차트로 자동 전환
  3. 가격 정보 업데이트
  ```

---

### ✅ 8. 코인 분석 패널 (Analysis Panel)

#### 8.1 가격 정보
- [ ] **코인명** - "비트코인 일봉"
- [ ] **현재 가격** (`#current-price`) - "₩174,715,000"
- [ ] **가격 변동** (`#price-change`)
  - 변동 금액: "1,255,000원"
  - 변동률: "+0.72%"
  - 색상: 상승(초록), 하락(빨강)

#### 8.2 기술적 분석
- [ ] **RSI**
  - 값: `#rsi-value` (0-100)
  - 상태: `#rsi-status`
    - 과매수 (70 이상)
    - 과매도 (30 이하)
    - 중립 (30-70)

- [ ] **이평선 값**
  - MA20, MA50, MA100, MA200
  - 천 단위 구분자 표시

#### 8.3 실시간 분석
- [ ] **추세** (`#trend-direction`)
  - 상승/하락/횡보

- [ ] **변동성** (`#volatility-level`)
  - 높음/보통/낮음

- [ ] **지지/저항** (`#support-level`, `#resistance-level`)
  - 가격 표시

- [ ] **매매 신호** (`#trading-signal`)
  - 매수/매도/관망

- [ ] **업데이트 시간** (`#update-time`)
  - 형식: "YYYY-MM-DD HH:MM:SS"

---

### ✅ 9. 모달 (Modals)

#### 9.1 매매이력 모달
- [ ] **열기/닫기**
  - 열기: `#show-history` 클릭
  - 닫기: `#close-history-modal` 또는 `#close-history-btn`

- [ ] **리스트 표시**
  - 거래 타입 (BUY/SELL)
  - 거래 시간
  - 가격

- [ ] **새로고침** (`#refresh-history`)

#### 9.2 그리기 목록 모달
- [ ] **열기/닫기**
  - 열기: `#show-drawings` 클릭
  - 닫기: `#close-drawings-modal` 또는 `#close-drawings-btn`

- [ ] **리스트 표시**
  - 그리기 타입
  - 생성 시간

- [ ] **개별 삭제**

#### 9.3 이평선 설정 모달
- [ ] **열기/닫기**
  - 열기: `#ma-settings-btn` 클릭
  - 닫기: `#close-ma-settings`

- [ ] **체크박스**
  - MA20, MA50, MA100, MA200, MA300, MA500, MA1000

- [ ] **적용/취소**
  - 적용: `#apply-ma-settings`
  - 취소: `#cancel-ma-settings`

---

## 알려진 이슈

### 해결 완료 ✅
1. **지지저항선 위치 오류** (2025-10-15)
   - 원인: 데이터 구조 불일치
   - 해결: `chartData` 구조 확인 및 수정

2. **지지저항선 토글 오류** (2025-10-15)
   - 원인: `ChartActions` 미초기화, 메서드 누락
   - 해결: `WorkingTradingChart`에 메서드 추가

### 진행 중 🔄
1. **미체결 주문 API 연동**
   - 상태: API 엔드포인트 구현 필요

2. **그리기 도구 구현**
   - 상태: 기본 UI만 있음, 실제 그리기 로직 없음

3. **SuperTrend 지표**
   - 상태: 버튼만 있음, 계산 로직 없음

---

## 문제 해결

### 1. 요소가 없다고 나올 때

```javascript
// 콘솔에서 확인
document.getElementById('요소ID');

// null이면 HTML 파일 확인
// 값이 있으면 CSS display 속성 확인
```

### 2. 버튼 클릭이 안 될 때

```javascript
// 이벤트 리스너 확인
const btn = document.getElementById('버튼ID');
console.log(getEventListeners(btn));

// 없으면 setupEventHandlers 호출 여부 확인
```

### 3. 차트가 렌더링 안 될 때

```javascript
// LightweightCharts 로드 확인
console.log(typeof LightweightCharts);

// 차트 인스턴스 확인
console.log(window.workingChart);
console.log(window.workingChart.chart);
```

### 4. 데이터 로딩 실패

```javascript
// API 서버 확인
fetch('http://localhost:8080/health')
  .then(r => r.json())
  .then(console.log);

// 네트워크 탭에서 요청 확인 (F12)
```

---

## 체크리스트 양식

### 검증 완료 보고서

```markdown
## 검증 일시
- 날짜: YYYY-MM-DD
- 시간: HH:MM
- 검증자: [이름]

## 검증 환경
- 브라우저: Chrome/Edge/Firefox
- 버전: [버전]
- OS: Windows/Mac/Linux

## 검증 결과
- 전체 기능: XX개
- 통과: XX개
- 실패: XX개
- 미검증: XX개

## 실패 항목
1. [기능명] - [실패 이유]
2. [기능명] - [실패 이유]

## 비고
[추가 의견]
```

---

## 다음 단계

1. ✅ 자동 검증 스크립트 완성
2. ✅ 체크리스트 작성
3. ⏳ 전체 기능 검증 실행
4. ⏳ 실패 항목 수정
5. ⏳ 재검증
6. ⏳ 최종 리포트 작성

---

## 참고 링크

- [FEATURE_CHECKLIST.md](./FEATURE_CHECKLIST.md) - 기능 목록
- [verify_features.html](http://localhost:8080/frontend/verify_features.html) - 자동 검증 도구
- [trading_chart.html](http://localhost:8080/frontend/trading_chart.html) - 메인 차트

---

**작성일**: 2025-10-15
**버전**: v1.0
**상태**: 활성
