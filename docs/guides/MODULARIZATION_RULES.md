# 모듈화 규칙 (2025.10.18 신규)

## 1. 모듈 분리 기준
- **파일 크기**: 500줄 초과 시 반드시 분리
- **기능 단위**: 하나의 모듈은 하나의 책임만
- **재사용성**: 다른 프로젝트에서도 사용 가능하도록

## 2. 모듈 작성 패턴
```javascript
// 모든 모듈은 클래스 기반으로 작성
class ModuleName {
    constructor(chartInstance) {
        this.chart = chartInstance;
        // 초기화
    }

    // Public 메서드
    publicMethod() {
        // 구현
    }
}

// Window에 노출 (필요시)
if (typeof window !== 'undefined') {
    window.ModuleName = ModuleName;
}
```

## 3. 모듈 간 통신
```javascript
// ✅ 올바른 방법: 명시적 의존성
class ModuleA {
    constructor(chartInstance) {
        this.chart = chartInstance;
    }
}

// ❌ 잘못된 방법: 전역 변수 직접 접근
class ModuleB {
    doSomething() {
        window.globalVar.method(); // 금지!
    }
}
```

## 4. 모듈 로딩 순서
```html
<!-- 1. 외부 라이브러리 -->
<script src="https://cdn.../lightweight-charts.js"></script>

<!-- 2. 유틸리티 모듈 -->
<script src="js/api_handler.js"></script>
<script src="js/chart_utils.js"></script>

<!-- 3. 기능 모듈 (의존성 없는 순서) -->
<script src="js/modules/actions/support_resistance.js"></script>
<script src="js/modules/actions/chart_actions.js"></script>
<script src="js/modules/indicators/technical_indicators.js"></script>

<!-- 4. 코어 모듈 (마지막) -->
<script src="js/core/trading_chart_core.js"></script>
```

## 5. 모듈화 체크리스트
개발 시 반드시 확인:
- [ ] 파일 크기 500줄 이하인가?
- [ ] 단일 책임 원칙 준수하는가?
- [ ] 순환 참조가 없는가?
- [ ] JSDoc 주석이 있는가?
- [ ] 독립적으로 테스트 가능한가?
- [ ] 전역 변수 오염이 없는가?

## 6. 에러 처리 패턴
모든 모듈은 일관된 에러 처리를 따라야 함:

```javascript
class ModuleName {
    methodName() {
        try {
            // 1. Input validation
            if (!this.chart || !this.chart.chartData) {
                console.warn('[ModuleName] Missing required data');
                return null; // Early return with safe value
            }

            // 2. Main logic
            const result = this.process();

            // 3. Success logging (optional)
            console.log('[ModuleName] Success:', result);
            return result;

        } catch (error) {
            // 4. Error logging with context
            console.error('[ModuleName] Error in methodName:', error);

            // 5. Graceful degradation (don't break the app)
            return null; // or default value
        }
    }
}
```

**에러 처리 규칙**:
- ✅ 모든 public 메서드는 try-catch 사용
- ✅ 에러 발생 시 앱이 중단되지 않도록 처리
- ✅ 콘솔 로그에 모듈명 접두사 사용 (예: `[SupportResistance]`)
- ✅ Input validation을 메서드 시작 부분에 배치
- ❌ 빈 catch 블록 금지 (최소한 console.error 필수)

## 7. 테스트 전략
각 모듈은 3단계 테스트 통과 필수:

### 7.1 단위 테스트 (Unit Test)
모듈 독립 실행 테스트:
```javascript
// test_module.html에서 개별 모듈 테스트
const module = new ModuleName(mockChart);
console.assert(module.method() !== undefined, 'Method should return value');
```

### 7.2 통합 테스트 (Integration Test)
다른 모듈과 함께 동작 테스트:
```javascript
// 메인 차트에서 모듈 통합
const chart = new TradingChart();
chart.moduleA.method();
// 다른 모듈이 정상 동작하는지 확인
```

### 7.3 시각 테스트 (Visual Test)
브라우저에서 육안 확인:
- ✅ 버튼 클릭 시 정상 동작
- ✅ 차트 업데이트 시 정상 반영
- ✅ 콘솔 에러 없음
- ✅ 메모리 누수 없음 (장시간 실행)

**테스트 파일 네이밍**:
- `test_[module_name].html` - 개별 모듈 테스트
- `test_integration.html` - 전체 통합 테스트

## 8. 성능 최적화 기준

### 8.1 파일 크기 목표
- 단일 모듈: 최대 500줄 (초과 시 재분리)
- HTML 파일: 최대 300줄
- CSS 파일: 최대 1000줄

### 8.2 실행 성능 목표
- 차트 초기 로딩: < 2초
- 코인 변경: < 1초
- 지표 토글: < 500ms
- 메모리 사용량: < 200MB (1시간 실행 후)

### 8.3 최적화 체크리스트
- [ ] 불필요한 재계산 방지 (캐싱 활용)
- [ ] DOM 조작 최소화
- [ ] 이벤트 리스너 적절히 해제
- [ ] 대용량 배열 처리 시 청크 단위 처리
- [ ] 콘솔 로그 과다 출력 금지 (production 환경)

## 9. Git 커밋 규칙

### 9.1 커밋 메시지 형식
```
[TYPE] Brief description (50 chars max)

Detailed explanation if needed (optional)
- Bullet point 1
- Bullet point 2
```

**TYPE 종류**:
- `[ADD]` - 새 기능 추가
- `[FIX]` - 버그 수정
- `[REFACTOR]` - 코드 리팩토링 (기능 변경 없음)
- `[MODULE]` - 모듈 추출/생성
- `[TEST]` - 테스트 코드 추가/수정
- `[DOCS]` - 문서 업데이트
- `[STYLE]` - 코드 포맷팅 (기능 변경 없음)

**예시**:
```
[MODULE] Extract SupportResistance module

- Created modules/actions/support_resistance.js (400 lines)
- Improved algorithm with ATR-based tolerance
- Added clustering and time-weighting
- Tested with test_modular.html
```

### 9.2 브랜치 전략
- `main` - 안정 버전 (배포 가능)
- `develop` - 개발 진행 중
- `feature/module-name` - 모듈 추출 작업
- `hotfix/issue-name` - 긴급 버그 수정

**규칙**:
- 직접 main에 커밋 금지
- 모든 변경은 feature 브랜치에서 작업
- 테스트 통과 후 develop으로 병합
- develop 안정화 후 main으로 병합

## 모듈 추출 퀵 가이드

### 모듈 추출 8단계 프로세스
상세 내용은 `MODULE_EXTRACTION_CHECKLIST.md` 참고

1. **모듈 파일 생성** → `modules/[category]/[name].js`
2. **모듈 구조 작성** → 클래스 기반 + JSDoc
3. **메서드 이식** → Prototype → Class 변환
4. **의존성 해결** → 명시적 참조로 변경
5. **상태 변수 이전** → Constructor에서 초기화
6. **테스트 코드 작성** → 독립 테스트 HTML
7. **HTML 통합** → 스크립트 태그 추가
8. **메인 차트 연결** → 모듈 인스턴스 생성

### 필수 검증 항목
- ✅ 파일 크기 < 500줄
- ✅ 기능 정상 동작
- ✅ 콘솔 에러 없음
- ✅ 하위 호환성 유지
- ✅ JSDoc 주석 완비
