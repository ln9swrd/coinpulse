# CoinPulse Trading Chart - 기능 체크리스트

## 작성일: 2025-10-15
## 버전: v20251015_0945

---

## 1. 헤더 섹션 (Header Row)

### 1.1 포트폴리오 정보 표시
- [ ] 장기 보유 코인 개수 표시 (`#long-term-count`)
- [ ] 단기 보유 코인 개수 표시 (`#short-term-count`)
- [ ] 투자 중인 코인 개수 표시 (`#investment-count`)
- [ ] 예산 금액 표시 (`#budget-amount`)
- [ ] 수익률 표시 (`#profit-rate`)

### 1.2 자동매매 컨트롤
- [ ] 보유코인 자동매매 토글 버튼 (`#holdings-auto-btn`)
  - 상태: 비활성화/활성화
  - 동작: 클릭 시 자동매매 시작/중지
- [ ] 단기투자 자동매매 토글 버튼 (`#active-auto-btn`)
  - 상태: 비활성화/활성화
  - 동작: 클릭 시 자동매매 시작/중지
- [ ] 정책 설정 버튼 (`#policy-btn`)
  - 동작: 정책 설정 페이지로 이동

---

## 2. 차트 설정 (Chart Settings)

### 2.1 기본 설정
- [ ] 차트 타입 선택 (`#chart-type`) - 현재 숨김
  - 캔들스틱
  - 라인
  - 영역
- [ ] 시간 프레임 선택 (`#timeframe`)
  - 1분, 5분, 15분
  - 1시간, 4시간
  - 일봉 (기본값)
  - 주봉
- [ ] 코인 검색 (`#coin-search`)
  - 실시간 검색 필터링
  - 한글명, 영문명, 코드 검색
- [ ] 코인 선택 (`#coin-select`)
  - 드롭다운으로 코인 선택
  - 차트 자동 업데이트
- [ ] 코인 목록 새로고침 (`#refresh-coins`)

---

## 3. 기술적 지표 (Technical Indicators)

### 3.1 이평선 (Moving Averages)
- [ ] 이평선 설정 버튼 (`#ma-settings-btn`)
  - 모달 열기/닫기
- [ ] MA 설정 모달
  - [ ] MA20 토글 (`#ma20-toggle`)
  - [ ] MA50 토글 (`#ma50-toggle`)
  - [ ] MA100 토글 (`#ma100-toggle`)
  - [ ] MA200 토글 (`#ma200-toggle`)
  - [ ] MA300 토글 (`#ma300-toggle`)
  - [ ] MA500 토글 (`#ma500-toggle`)
  - [ ] MA1000 토글 (`#ma1000-toggle`)
  - [ ] 적용 버튼 (`#apply-ma-settings`)
  - [ ] 취소 버튼 (`#cancel-ma-settings`)

### 3.2 기타 지표
- [ ] RSI 토글 (`#rsi-toggle`)
  - 독립 패널 표시/숨김
  - RSI 계산 및 차트 렌더링
- [ ] MACD 토글 (`#macd-toggle`)
  - 독립 패널 표시/숨김
  - MACD, Signal, Histogram 표시
- [ ] Bollinger Bands 토글 (`#bollinger-toggle`)
  - 메인 차트에 밴드 표시
- [ ] SuperTrend 토글 (`#supertrend-toggle`)
  - 메인 차트에 슈퍼트렌드 표시

---

## 4. 그리기 도구 (Drawing Tools)

### 4.1 기본 그리기
- [ ] 추세선 그리기 (`#draw-trendline`)
  - 클릭 후 차트에 2개 점 선택
  - 추세선 생성
- [ ] 피보나치 되돌림 (`#draw-fibonacci`)
  - 시작점/끝점 선택
  - 피보나치 레벨 표시
- [ ] 수평선 그리기 (`#draw-horizontal`)
  - 가격 레벨에 수평선 추가
- [ ] 수직선 그리기 (`#draw-vertical`)
  - 시간 레벨에 수직선 추가

### 4.2 그리기 관리
- [ ] 모두 지우기 버튼 (`#clear-trendlines`)
  - 모든 그리기 삭제
- [ ] 그리기 목록 버튼 (`#show-drawings`)
  - 그리기 목록 모달 열기
  - 개별 항목 삭제 가능

---

## 5. 차트 액션 (Chart Actions)

### 5.1 테마 및 표시 옵션
- [ ] 테마 토글 (`#theme-toggle`)
  - 다크/라이트 테마 전환
  - localStorage에 저장
- [ ] 지지저항선 토글 (`#support-resistance-toggle`)
  - 지지/저항 레벨 자동 계산
  - 차트에 수평선 표시
- [ ] 이평선 토글 (`#ma-toggle`)
  - 모든 이평선 표시/숨김
- [ ] 매매마커 토글 (`#trade-markers-toggle`)
  - 매수/매도 마커 표시
  - 기본값: 활성화
- [ ] 거래량 토글 (`#volume-toggle`)
  - 거래량 차트 표시/숨김

### 5.2 데이터 조회
- [ ] 매매이력 버튼 (`#show-history`)
  - 매매이력 모달 열기
  - 과거 거래 내역 표시
- [ ] 미체결 토글 (`#pending-order-toggle`)
  - 미체결 주문 마커 표시

---

## 6. 차트 렌더링 (Chart Rendering)

### 6.1 메인 차트
- [ ] 캔들스틱 차트 렌더링 (`#chart-container`)
  - LightweightCharts 라이브러리 사용
  - 실시간 데이터 업데이트
- [ ] 거래량 차트
  - 메인 차트 하단에 표시
  - 색상: 상승(초록), 하락(빨강)

### 6.2 보조 차트
- [ ] RSI 차트 (`#rsi-container`)
  - 독립 패널
  - 과매수/과매도 레벨 표시
- [ ] MACD 차트 (`#macd-container`)
  - 독립 패널
  - MACD Line, Signal Line, Histogram

### 6.3 TradingView 방식 로딩
- [ ] 초기 200개 캔들 로딩
- [ ] 스크롤 시 과거 데이터 자동 로딩
- [ ] 중복 데이터 필터링
- [ ] 자동 업데이트 (30초 간격)

---

## 7. 보유 코인 패널 (Holdings Panel)

### 7.1 보유 코인 목록
- [ ] 보유 코인 리스트 표시 (`#holdings-list`)
  - 코인명
  - 평균단가
  - 수익률
- [ ] 새로고침 버튼 (`#refresh-holdings`)
  - 보유 코인 데이터 갱신

### 7.2 클릭 액션
- [ ] 코인 클릭 시 해당 코인 차트로 전환

---

## 8. 코인 분석 패널 (Analysis Panel)

### 8.1 가격 정보
- [ ] 코인명 표시
- [ ] 현재 가격 표시 (`#current-price`)
- [ ] 가격 변동 표시 (`#price-change`)
  - 변동 금액 (`#change-amount`)
  - 변동률 (`#change-rate`)
  - 색상: 상승(초록), 하락(빨강)

### 8.2 기술적 분석
- [ ] RSI 값 표시 (`#rsi-value`)
- [ ] RSI 상태 (`#rsi-status`)
  - 과매수/과매도/중립
- [ ] 이평선 값 표시
  - MA20 (`#ma20-value`)
  - MA50 (`#ma50-value`)
  - MA100 (`#ma100-value`)
  - MA200 (`#ma200-value`)

### 8.3 실시간 분석
- [ ] 추세 방향 (`#trend-direction`)
  - 상승/하락/횡보
- [ ] 변동성 레벨 (`#volatility-level`)
  - 높음/보통/낮음
- [ ] 지지 레벨 (`#support-level`)
- [ ] 저항 레벨 (`#resistance-level`)
- [ ] 매매 신호 (`#trading-signal`)
  - 매수/매도/관망
- [ ] 업데이트 시간 (`#update-time`)

---

## 9. 모달 (Modals)

### 9.1 매매이력 모달 (`#history-modal`)
- [ ] 모달 열기 (`#show-history` 클릭)
- [ ] 매매이력 리스트 표시
  - 거래 타입 (매수/매도)
  - 거래 시간
- [ ] 새로고침 버튼 (`#refresh-history`)
- [ ] 닫기 버튼 (`#close-history-modal`, `#close-history-btn`)

### 9.2 그리기 목록 모달 (`#drawings-modal`)
- [ ] 모달 열기 (`#show-drawings` 클릭)
- [ ] 그리기 목록 표시
  - 그리기 타입
  - 생성 시간
- [ ] 개별 항목 삭제
- [ ] 새로고침 버튼 (`#refresh-drawings`)
- [ ] 닫기 버튼 (`#close-drawings-modal`, `#close-drawings-btn`)

### 9.3 이평선 설정 모달 (`#ma-settings-modal`)
- [ ] 모달 열기 (`#ma-settings-btn` 클릭)
- [ ] 체크박스로 이평선 선택
- [ ] 적용 버튼으로 설정 저장
- [ ] 취소 버튼으로 변경사항 무시
- [ ] 닫기 버튼 (`#close-ma-settings`)

---

## 10. 로딩 상태 (Loading States)

### 10.1 로딩 오버레이
- [ ] 로딩 오버레이 표시 (`#loading-overlay`)
  - 초기 로딩 시 표시
  - 데이터 로딩 완료 시 숨김
- [ ] 로딩 스피너 애니메이션
- [ ] 로딩 텍스트 표시

---

## 검증 방법

### 자동 검증
```bash
# 브라우저에서 실행
node verify_features.js
```

### 수동 검증
1. 브라우저 콘솔 열기 (F12)
2. 각 기능 버튼 클릭
3. 콘솔 로그 확인
4. UI 변화 관찰

---

## 우선순위

### High Priority (핵심 기능)
1. 차트 렌더링
2. 코인 선택 및 전환
3. 시간 프레임 변경
4. 거래량 표시
5. 이평선 표시

### Medium Priority (중요 기능)
1. 지지저항선
2. RSI/MACD 지표
3. 매매마커
4. 보유 코인 목록
5. 테마 전환

### Low Priority (부가 기능)
1. 그리기 도구
2. 미체결 주문
3. 매매이력
4. SuperTrend
5. Bollinger Bands

---

## 알려진 이슈

### 해결 완료
- [x] 지지저항선 위치 오류 → 수정 완료 (2025-10-15)
- [x] 지지저항선 토글 오류 → 수정 완료 (2025-10-15)

### 진행 중
- [ ] 미체결 주문 API 연동
- [ ] 그리기 도구 구현
- [ ] SuperTrend 지표 구현

---

## 다음 단계

1. 자동 검증 스크립트 작성
2. 각 기능별 단위 테스트
3. 통합 테스트
4. 사용자 피드백 수집
