# 코인펄스 코딩 가이드라인

## 📋 인코딩 규칙

### ✅ 허용되는 파일 타입

#### HTML 파일 (`.html`)
- ✅ **이모지 사용 가능**
- ✅ **한글 사용 가능**
- 용도: 사용자 인터페이스, 문서화
- 예시:
  ```html
  <button>📊 차트 보기</button>
  <h1>코인펄스 트레이딩 시스템</h1>
  ```

#### Markdown 파일 (`.md`)
- ✅ **이모지 사용 가능**
- ✅ **한글 사용 가능**
- 용도: 문서화, README, 가이드
- 예시:
  ```markdown
  ## 🚀 시작하기
  코인펄스를 설치하려면...
  ```

---

### ⚠️ 제한되는 파일 타입

#### Python 파일 (`.py`)
- ❌ **이모지 사용 금지**
- ❌ **한글 주석/문자열 사용 금지** (docstring 포함)
- ✅ **영문만 사용**
- 이유: Windows cp949 콘솔 출력 시 인코딩 오류 발생
- 예시:
  ```python
  # Good
  def start_server():
      """Start the trading server"""
      print("Server started successfully")
  
  # Bad
  def start_server():
      """서버를 시작합니다"""  # 한글 금지
      print("✅ 서버 시작 완료")  # 이모지 금지
  ```

#### JavaScript 파일 (`.js`)
- ❌ **이모지 사용 금지**
- ❌ **한글 주석/문자열 사용 금지**
- ✅ **영문만 사용**
- 이유: 콘솔 로그 및 에러 메시지 출력 시 인코딩 문제
- 예시:
  ```javascript
  // Good
  console.log("[OK] Chart loaded successfully");
  const status = isRunning ? "Running" : "Stopped";
  
  // Bad
  console.log("📊 차트 로드 완료");  // 이모지 금지
  const status = isRunning ? "실행중" : "중지됨";  // 한글 금지
  ```

#### CSS 파일 (`.css`)
- ❌ **이모지 사용 금지**
- ⚠️ **한글 주석 최소화**
- ✅ **영문 권장**

#### JSON 파일 (`.json`)
- ❌ **이모지 사용 금지**
- ⚠️ **키 이름은 영문 권장**
- ✅ **값(value)에 한글 사용 가능** (사용자 표시용)
- 예시:
  ```json
  {
    "server": {
      "name": "Chart Server",
      "description": "Upbit chart data API server"
    }
  }
  ```

---

## 🔍 자동 검사

### Unicode 이모지 검사 스크립트

```bash
# 수동 검사
python check_unicode.py

# 서비스 시작 시 자동 검사 (경고만 표시)
python service_manager.py start
```

### 검사 대상
- ✅ `.py` - Python 실행 파일
- ✅ `.js` - JavaScript 실행 파일
- ✅ `.css` - 스타일시트
- ✅ `.json` - 설정 파일
- ❌ `.html` - 검사 제외
- ❌ `.md` - 검사 제외

---

## 📝 권장 사항

### 1. 로그 메시지
```python
# Good
self.log("Service started successfully")
self.log("[WARNING] Port already in use")
self.log("[ERROR] Failed to connect to API")

# Bad
self.log("✅ 서비스 시작 완료")
self.log("⚠️ 포트가 이미 사용중입니다")
```

### 2. 상태 표시
```javascript
// Good
btn.textContent = isEnabled ? "[ON] Feature" : "[OFF] Feature";
const icon = isSuccess ? "[OK]" : "[ERROR]";

// Bad
btn.textContent = isEnabled ? "✅ 기능 켜짐" : "❌ 기능 꺼짐";
const icon = isSuccess ? "✅" : "❌";
```

### 3. 주석
```python
# Good - English comments
# Initialize the trading engine
# This function handles API requests

# Bad - Korean comments
# 트레이딩 엔진 초기화
# 이 함수는 API 요청을 처리합니다
```

### 4. 변수/함수 이름
```python
# Good - English names
def calculate_moving_average():
    total_price = 0
    is_running = True

# Bad - Korean transliteration
def gyesan_idongpyeonggyun():  # 피하기
    chong_gagyeok = 0
```

---

## 🛠️ 예외 사항

### 외부 라이브러리
- `lightweight-charts.standalone.production.js` - 검사 제외
- 기타 third-party 라이브러리 - 검사 제외

### 백업 폴더
- `backup_*` - 검사 제외
- 테스트 파일 - 필요시 개별 제외

---

## 📚 참고

### Windows cp949 인코딩 문제
Windows 한글 환경에서는 기본 콘솔 인코딩이 cp949입니다. 
Python이나 JavaScript의 `print()` 또는 `console.log()`에서 
UTF-8 이모지나 한글을 출력하면 `UnicodeEncodeError`가 발생할 수 있습니다.

### 해결 방법
1. **실행 파일**: 영문만 사용 (근본적 해결)
2. **문서 파일**: UTF-8로 저장, 이모지/한글 자유롭게 사용
3. **설정 파일**: JSON 값에는 한글 가능, 키는 영문 권장

---

## ✅ 체크리스트

새 코드 작성 시:
- [ ] Python 파일에 한글/이모지가 없는가?
- [ ] JavaScript 파일에 한글/이모지가 없는가?
- [ ] 로그 메시지가 모두 영문인가?
- [ ] 주석이 영문으로 작성되었는가?
- [ ] HTML/MD 파일만 한글/이모지를 사용했는가?
- [ ] `python check_unicode.py` 검사를 통과하는가?

---

**마지막 업데이트**: 2025-10-14


