# 🚀 진행중인 기능 완성 가이드

**작성일**: 2025-12-14
**대상**: 텔레그램 봇 + 대시보드 급등 예측 통합
**예상 소요**: 2-3시간

---

## 📋 완성 대상

### 1. ✅ 텔레그램 알림 봇 시스템
- **현황**: 코드 100% 완성, 토큰 설정만 필요
- **파일**:
  - `backend/services/telegram_bot.py` ✅
  - `backend/services/surge_alert_scheduler.py` ✅
  - `docs/TELEGRAM_BOT_GUIDE.md` ✅

### 2. 🟡 대시보드 급등 예측 통합
- **현황**: 별도 페이지 존재, 대시보드 통합 필요
- **파일**:
  - `frontend/surge_monitoring.html` ✅
  - `frontend/dashboard.html` (수정 필요)

---

## 🔧 작업 1: 텔레그램 봇 활성화

### 1.1 봇 생성 (5분)

1. **텔레그램 앱 실행**
2. **@BotFather 검색**
3. 명령어 입력:
   ```
   /newbot
   ```
4. **봇 이름 입력**:
   ```
   CoinPulse 급등 알림
   ```
5. **봇 사용자명 입력** (고유해야 함):
   ```
   coinpulse_surge_alert_bot
   ```
6. **봇 토큰 복사** (예시):
   ```
   7482916535:AAH8Rj3mKqp9xVUY4HZb7xdoIrxkSFUfafQK
   ```

### 1.2 프로덕션 환경 변수 설정 (2분)

```bash
# SSH 접속
ssh root@158.247.222.216

# .env 파일 편집
cd /opt/coinpulse
nano .env

# TELEGRAM_BOT_TOKEN 줄 찾아서 토큰 입력
TELEGRAM_BOT_TOKEN=발급받은_토큰_여기에_붙여넣기

# 저장: Ctrl+O, Enter
# 종료: Ctrl+X
```

### 1.3 systemd 서비스 파일 생성 (5분)

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/coinpulse-telegram.service
```

**내용**:
```ini
[Unit]
Description=CoinPulse Telegram Alert Bot
After=network.target coinpulse.service
Requires=coinpulse.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/coinpulse
Environment="PATH=/opt/coinpulse/venv/bin"
EnvironmentFile=/opt/coinpulse/.env
ExecStart=/opt/coinpulse/venv/bin/python backend/services/surge_alert_scheduler.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/coinpulse/logs/telegram_bot.log
StandardError=append:/opt/coinpulse/logs/telegram_bot.log

[Install]
WantedBy=multi-user.target
```

저장 후:
```bash
# 권한 설정
sudo chmod 644 /etc/systemd/system/coinpulse-telegram.service

# systemd 리로드
sudo systemctl daemon-reload

# 서비스 활성화
sudo systemctl enable coinpulse-telegram

# 서비스 시작
sudo systemctl start coinpulse-telegram

# 상태 확인
sudo systemctl status coinpulse-telegram
```

### 1.4 봇 테스트 (3분)

1. **텔레그램 앱에서 봇 검색**:
   ```
   @coinpulse_surge_alert_bot
   ```

2. **명령어 테스트**:
   ```
   /start
   /status
   /stats
   /help
   ```

3. **로그 확인**:
   ```bash
   tail -f /opt/coinpulse/logs/telegram_bot.log
   ```

### 1.5 알림 작동 확인 (대기)

- 봇은 **5분마다** 자동으로 급등 후보를 체크합니다
- 60점 이상 코인 발견 시 자동 알림 전송
- 중복 알림 방지 (같은 코인은 한 번만)

---

## 🎨 작업 2: 대시보드 급등 예측 통합

### 2.1 대시보드에 Quick Link 추가

#### 방법 A: 수동 편집 (권장)

```bash
ssh root@158.247.222.216
nano /opt/coinpulse/frontend/dashboard.html
```

**찾기** (Ctrl+W):
```html
<a href="/policy_manager.html" class="quick-link">
```

**바로 다음 줄에 추가**:
```html
<a href="/surge_monitoring.html" class="quick-link">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
    </svg>
    <span>Surge Prediction</span>
</a>
```

#### 방법 B: sed 명령 (빠름)

```bash
ssh root@158.247.222.216 "cd /opt/coinpulse && \
sed -i '/<a href=\"\/policy_manager.html\" class=\"quick-link\">/a\
                                    <a href=\"/surge_monitoring.html\" class=\"quick-link\">\
                                        <svg width=\"20\" height=\"20\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\">\
                                            <path d=\"M13 2L3 14h9l-1 8 10-12h-9l1-8z\"/>\
                                        </svg>\
                                        <span>Surge Prediction</span>\
                                    </a>' frontend/dashboard.html"
```

### 2.2 메인 네비게이션에 메뉴 추가 (선택)

```html
<!-- 찾기: <a href="#settings" class="nav-item" -->
<!-- 바로 다음 줄에 추가 -->

<a href="#surge-prediction" class="nav-item" data-page="surge-prediction">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
    </svg>
    <span>Surge Prediction</span>
</a>
```

### 2.3 대시보드 Overview에 위젯 추가 (고급)

**파일**: `frontend/dashboard.html`

**위치**: Overview 섹션의 카드 그리드

**추가 코드**:
```html
<!-- Surge Prediction Widget -->
<div class="stats-card">
    <div class="card-header">
        <h3>급등 예측</h3>
        <a href="/surge_monitoring.html" class="view-all">전체 보기</a>
    </div>
    <div class="card-content" id="surge-widget">
        <div class="loading-state">
            <div class="spinner"></div>
            <p>급등 후보 검색 중...</p>
        </div>
    </div>
</div>
```

**JavaScript 추가** (dashboard.html 하단):
```javascript
// Surge Prediction Widget
async function loadSurgeCandidates() {
    try {
        const response = await fetch('/api/surge-candidates');
        const data = await response.json();

        const widget = document.getElementById('surge-widget');

        if (data.candidates && data.candidates.length > 0) {
            // 상위 3개만 표시
            const top3 = data.candidates.slice(0, 3);

            widget.innerHTML = `
                <div class="surge-list">
                    ${top3.map(c => `
                        <div class="surge-item">
                            <div class="surge-coin">${c.market}</div>
                            <div class="surge-score ${c.score >= 70 ? 'high' : ''}">${c.score}점</div>
                            <div class="surge-price">${c.current_price.toLocaleString()}원</div>
                        </div>
                    `).join('')}
                </div>
                <div class="widget-stats">
                    <small>백테스트 적중률: ${data.backtest_stats.win_rate}%</small>
                </div>
            `;
        } else {
            widget.innerHTML = `
                <div class="empty-state">
                    <p>현재 급등 후보가 없습니다</p>
                    <small>5분마다 자동 갱신됩니다</small>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load surge candidates:', error);
    }
}

// 페이지 로드 시 & 5분마다 갱신
if (window.location.hash === '#overview' || !window.location.hash) {
    loadSurgeCandidates();
    setInterval(loadSurgeCandidates, 5 * 60 * 1000);
}
```

**CSS 추가** (dashboard.css 또는 inline style):
```css
.surge-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.surge-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: var(--card-bg);
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.surge-coin {
    font-weight: 600;
    color: var(--text-primary);
}

.surge-score {
    padding: 4px 12px;
    border-radius: 12px;
    background: var(--success-bg);
    color: var(--success-color);
    font-weight: 600;
    font-size: 14px;
}

.surge-score.high {
    background: var(--primary-bg);
    color: var(--primary-color);
}

.surge-price {
    color: var(--text-secondary);
    font-size: 14px;
}

.widget-stats {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--border-color);
    text-align: center;
}

.empty-state {
    text-align: center;
    padding: 32px 16px;
    color: var(--text-secondary);
}
```

---

## 🎯 작업 3: 알림 설정 UI 추가 (고급)

### 3.1 Settings 페이지에 텔레그램 연동 섹션 추가

**파일**: `frontend/dashboard.html` (Settings 섹션)

```html
<div class="settings-section">
    <h3>알림 설정</h3>

    <!-- 텔레그램 연동 -->
    <div class="setting-item">
        <div class="setting-info">
            <h4>텔레그램 알림</h4>
            <p>급등 예측 알림을 텔레그램으로 받으세요</p>
        </div>
        <div class="setting-actions">
            <button class="btn-primary" onclick="window.open('https://t.me/coinpulse_surge_alert_bot', '_blank')">
                봇 연결하기
            </button>
        </div>
    </div>

    <!-- 알림 주기 설정 -->
    <div class="setting-item">
        <div class="setting-info">
            <h4>알림 최소 점수</h4>
            <p>설정한 점수 이상일 때만 알림을 받습니다</p>
        </div>
        <div class="setting-actions">
            <select id="alert-threshold">
                <option value="60">60점 이상</option>
                <option value="70">70점 이상</option>
                <option value="80">80점 이상</option>
            </select>
        </div>
    </div>
</div>
```

### 3.2 백테스트 결과 링크 추가

```html
<div class="setting-item">
    <div class="setting-info">
        <h4>검증 결과</h4>
        <p>급등 예측 알고리즘의 백테스트 결과를 확인하세요</p>
    </div>
    <div class="setting-actions">
        <a href="/backtest_results.html" class="btn-secondary" target="_blank">
            백테스트 결과 보기
        </a>
    </div>
</div>
```

---

## ✅ 완성 체크리스트

### 텔레그램 봇
- [ ] @BotFather에서 봇 생성 완료
- [ ] 봇 토큰 발급 받음
- [ ] `.env` 파일에 토큰 설정
- [ ] systemd 서비스 파일 생성
- [ ] 서비스 활성화 및 시작
- [ ] `/start` 명령어 테스트
- [ ] 로그 확인 (에러 없음)
- [ ] 급등 알림 수신 확인 (대기)

### 대시보드 통합
- [ ] Quick Link에 "Surge Prediction" 추가
- [ ] 링크 클릭 시 surge_monitoring.html 정상 작동
- [ ] (선택) 메인 네비게이션 메뉴 추가
- [ ] (선택) Overview 위젯 추가
- [ ] (선택) Settings에 알림 설정 UI 추가
- [ ] (선택) 백테스트 결과 링크 추가

### 최종 확인
- [ ] 대시보드 로그인 가능
- [ ] 급등 예측 페이지 접근 가능
- [ ] API `/api/surge-candidates` 정상 응답
- [ ] 텔레그램 봇 응답 정상
- [ ] 로그에 에러 없음

---

## 🐛 트러블슈팅

### 문제 1: 텔레그램 봇 시작 안됨

**증상**:
```bash
systemctl status coinpulse-telegram
# Active: failed
```

**해결**:
```bash
# 로그 확인
journalctl -u coinpulse-telegram -n 50

# 환경 변수 확인
cat /opt/coinpulse/.env | grep TELEGRAM

# 수동 실행 테스트
cd /opt/coinpulse
source venv/bin/activate
python backend/services/surge_alert_scheduler.py
```

### 문제 2: 알림이 오지 않음

**원인**:
1. 급등 후보가 실제로 없음 (60점 이상)
2. `/start` 명령어를 보내지 않음
3. 이미 알림 받은 코인 (중복 방지)

**확인**:
```bash
# API 직접 호출
curl -s https://coinpulse.sinsi.ai/api/surge-candidates | python -m json.tool

# 로그 확인
tail -f /opt/coinpulse/logs/telegram_bot.log
```

### 문제 3: 대시보드 Quick Link 깨짐

**증상**: HTML 구조가 깨져서 페이지가 제대로 안보임

**해결**:
```bash
# 백업에서 복원
ssh root@158.247.222.216
cd /opt/coinpulse/frontend
cp dashboard.html.production dashboard.html

# 다시 신중하게 수정
nano dashboard.html
```

---

## 📊 예상 효과

### 사용자 경험 개선
- ✅ 대시보드에서 급등 예측 1클릭 접근
- ✅ 텔레그램으로 실시간 알림 수신
- ✅ 모바일에서도 즉시 확인 가능

### 전환율 향상
- 📈 무료 → 유료 전환율 +15% 예상
- 📈 알림 기능으로 재방문율 +40% 예상
- 📈 텔레그램 커뮤니티 형성 가능

---

## 🎯 다음 단계

완성 후:
1. **베타 테스터 모집** (50-100명)
2. **실시간 적중률 추적** 시작
3. **피드백 수집** 및 개선
4. **유료 플랜 전환** 준비 (3개월 후)

---

**최종 업데이트**: 2025-12-14
**예상 완성 시간**: 2-3시간
**난이도**: ⭐⭐⭐ (중급)
