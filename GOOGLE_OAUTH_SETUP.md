# Google OAuth 설정 가이드

## 📋 개요

CoinPulse에 Google 로그인 기능이 추가되었습니다. 아래 단계를 따라 Google Cloud Console에서 OAuth 클라이언트 ID를 발급받고 설정하세요.

---

## 🔧 1단계: Google Cloud Console 설정

### 1.1 프로젝트 생성 (또는 기존 프로젝트 선택)

1. **Google Cloud Console** 접속: https://console.cloud.google.com/
2. 상단의 프로젝트 선택 드롭다운 클릭
3. **새 프로젝트** 클릭
4. 프로젝트 이름 입력: `CoinPulse` (또는 원하는 이름)
5. **만들기** 클릭

### 1.2 OAuth 동의 화면 구성

1. 왼쪽 메뉴에서 **API 및 서비스 > OAuth 동의 화면** 선택
2. **사용자 유형** 선택:
   - **외부** 선택 (누구나 Google 계정으로 로그인 가능)
   - **만들기** 클릭

3. **OAuth 동의 화면 정보 입력**:
   ```
   앱 이름: CoinPulse
   사용자 지원 이메일: [귀하의 이메일]
   앱 로고: (선택사항)
   앱 도메인:
     - 애플리케이션 홈페이지: http://localhost:8080 (개발) 또는 https://coinpulse.sinsi.ai (프로덕션)
     - 개인정보처리방침: (선택사항)
     - 서비스 약관: (선택사항)
   개발자 연락처 정보: [귀하의 이메일]
   ```

4. **범위** 설정:
   - **범위 추가 또는 삭제** 클릭
   - 다음 범위 선택:
     - `./auth/userinfo.email`
     - `./auth/userinfo.profile`
     - `openid`
   - **업데이트** 클릭

5. **테스트 사용자** (선택사항):
   - 개발 단계에서는 테스트 사용자를 추가할 수 있습니다
   - 이메일 주소를 입력하고 **추가** 클릭

6. **저장 후 계속** 클릭

### 1.3 OAuth 클라이언트 ID 생성

1. 왼쪽 메뉴에서 **API 및 서비스 > 사용자 인증 정보** 선택
2. 상단의 **+ 사용자 인증 정보 만들기** 클릭
3. **OAuth 클라이언트 ID** 선택

4. **애플리케이션 유형**: **웹 애플리케이션** 선택

5. **이름**: `CoinPulse Web Client` (또는 원하는 이름)

6. **승인된 자바스크립트 원본** 추가:
   ```
   http://localhost:8080
   http://127.0.0.1:8080
   https://coinpulse.sinsi.ai (프로덕션)
   ```

7. **승인된 리디렉션 URI** (선택사항, 필요 없음):
   - 현재 구현은 팝업 방식이므로 리디렉션 URI가 필요 없습니다

8. **만들기** 클릭

9. **클라이언트 ID 복사**:
   ```
   예시: 123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com
   ```

---

## 🔑 2단계: 클라이언트 ID 적용

### 2.1 login.html 파일 수정

1. 파일 위치: `D:\Claude\Projects\Active\coinpulse\frontend\login.html`

2. 102번째 줄 찾기:
   ```html
   data-client_id="YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
   ```

3. `YOUR_GOOGLE_CLIENT_ID` 부분을 복사한 클라이언트 ID로 교체:
   ```html
   data-client_id="123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com"
   ```

4. 파일 저장 (Ctrl + S)

---

## 🚀 3단계: 서버 재시작 및 테스트

### 3.1 서버 재시작

Windows 환경:
```cmd
# 기존 서버 중지
taskkill /F /IM python.exe

# 서버 시작
python app.py
```

또는 배치 파일 사용:
```cmd
QUICK_START.bat
```

### 3.2 테스트

1. 브라우저에서 로그인 페이지 열기:
   ```
   http://localhost:8080/login.html
   ```

2. **Google로 계속하기** 버튼 클릭

3. Google 계정 선택 팝업이 나타나는지 확인

4. 계정 선택 후 자동으로 로그인되는지 확인

5. 대시보드로 리디렉션되는지 확인

---

## ✅ 작동 원리

### 사용자 흐름:

1. **버튼 클릭**: "Google로 계속하기" 클릭
2. **Google 팝업**: Google 계정 선택 창 표시
3. **계정 선택**: 사용자가 Google 계정 선택
4. **JWT 토큰**: Google이 JWT 크리덴셜 생성
5. **백엔드 전송**: `POST /api/auth/google-login`으로 토큰 전송
6. **사용자 확인**:
   - **기존 사용자**: 로그인 처리
   - **신규 사용자**: 자동 회원가입 후 로그인
7. **토큰 발급**: CoinPulse JWT 토큰 발급
8. **리디렉션**: `/dashboard.html`로 이동

### 백엔드 처리:

```python
POST /api/auth/google-login
{
  "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6...",
  "email": "user@gmail.com",
  "name": "John Doe",
  "picture": "https://..."
}

Response:
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "user": { ... }
}
```

---

## 🔒 보안 참고사항

### 현재 구현 (개발 버전):

- ✅ Google JWT 토큰 수신
- ⚠️ 클라이언트에서 디코딩한 이메일 신뢰
- ⚠️ **프로덕션에는 적합하지 않음**

### 프로덕션 권장 사항:

백엔드에서 Google JWT 토큰을 직접 검증해야 합니다.

**필요한 패키지 설치**:
```bash
pip install google-auth
```

**auth_routes.py 수정** (705-710번째 줄):

현재 코드:
```python
# TODO: Verify Google JWT credential with google-auth library
# For now, we trust the email from the client (not recommended for production)
```

프로덕션 코드:
```python
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

GOOGLE_CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"

try:
    # Verify the token
    idinfo = id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        GOOGLE_CLIENT_ID
    )

    # Get verified email
    email = idinfo['email']
    name = idinfo.get('name', '')
    picture = idinfo.get('picture', '')

except ValueError:
    # Invalid token
    return jsonify({
        'success': False,
        'error': 'Invalid Google token',
        'code': 'INVALID_TOKEN'
    }), 401
```

---

## 🐛 문제 해결

### 1. "Google 로그인 서비스를 불러오는 중입니다" 에러

**원인**: Google SDK가 로드되지 않음

**해결**:
- 인터넷 연결 확인
- 브라우저 콘솔 (F12) 에서 네트워크 탭 확인
- `https://accounts.google.com/gsi/client` 로드 실패 확인

### 2. 팝업이 나타나지 않음

**원인**:
- 클라이언트 ID가 올바르지 않음
- 브라우저 팝업 차단

**해결**:
- login.html에서 클라이언트 ID 다시 확인
- 브라우저 팝업 차단 해제
- 브라우저 콘솔에서 에러 메시지 확인

### 3. "승인되지 않은 원본" 에러

**원인**: Google Cloud Console에서 승인된 자바스크립트 원본이 설정되지 않음

**해결**:
- Google Cloud Console → OAuth 클라이언트 ID 편집
- 승인된 자바스크립트 원본에 `http://localhost:8080` 추가
- 변경사항 저장 (최대 5분 소요)

### 4. "redirect_uri_mismatch" 에러

**원인**: 리디렉션 URI 불일치 (현재 구현에서는 발생하지 않아야 함)

**해결**:
- 팝업 모드 (`data-ux_mode="popup"`)를 사용하므로 리디렉션 URI가 필요 없음
- 혹시 에러가 발생하면 Google Cloud Console에서 리디렉션 URI 확인

---

## 📚 추가 자료

- [Google Identity 문서](https://developers.google.com/identity/gsi/web/guides/overview)
- [OAuth 2.0 개요](https://developers.google.com/identity/protocols/oauth2)
- [JWT 토큰 검증](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token)

---

## 🎯 다음 단계 (선택사항)

1. **프로덕션 배포 시**:
   - 백엔드에서 JWT 토큰 검증 추가 (위 보안 참고사항 참조)
   - HTTPS 사용 (Google OAuth는 HTTPS 권장)
   - 환경 변수로 클라이언트 ID 관리

2. **추가 기능**:
   - Google 프로필 사진을 사용자 아바타로 사용
   - 구글 계정 연동 해제 기능
   - 여러 로그인 방법 병합 (이메일 + Google 동일 계정)

---

## ✅ 체크리스트

- [ ] Google Cloud Console에서 프로젝트 생성
- [ ] OAuth 동의 화면 구성
- [ ] OAuth 클라이언트 ID 생성
- [ ] 클라이언트 ID 복사
- [ ] login.html에서 CLIENT_ID 교체
- [ ] 서버 재시작
- [ ] 테스트 로그인 성공
- [ ] 프로덕션 배포 시 JWT 검증 추가

---

**작성일**: 2025-12-18
**버전**: 1.0
**문의**: support@coinpulse.com
