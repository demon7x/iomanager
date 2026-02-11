# Shotgun 프로젝트 선택 UI - 구현 요약

## ✅ 완료된 작업

### 신규 파일 (3개)

1. **`python/app/ui/project_selector.py`**
   - `ProjectSelectorDialog` 클래스 (QDialog)
   - `show_project_selector()` 헬퍼 함수
   - Shotgun 프로젝트 그리드 UI (240x144 썸네일)

2. **`python/app/utils/thumbnail_loader.py`**
   - `download_thumbnail()`: URL에서 썸네일 다운로드
   - `create_placeholder()`: 플레이스홀더 생성
   - `_get_initials()`: 프로젝트 이니셜 추출

3. **테스트 파일**
   - `test_imports.py`: 모든 모듈 임포트 검증 ✓
   - `test_project_selector.py`: UI 테스트 (Mock Shotgun)

### 수정된 파일 (3개)

1. **`python/app/__init__.py`**
   - `AppInstance.update_project_context()` 메서드 추가
   - 런타임에 프로젝트 Context 업데이트

2. **`app.py`**
   - `_handle_project_selection()` 메서드 추가
   - `run()` 메서드에 프로젝트 선택 흐름 통합

3. **`python/app/utils/qt_compat.py`**
   - `QListWidgetItem` 임포트 추가
   - 호환성 패치 리스트 업데이트

## 🎯 구현 내용

### 주요 기능

- ✅ Shotgun에서 활성 프로젝트 자동 로드
- ✅ 썸네일 그리드 UI (3열 레이아웃)
- ✅ 썸네일 다운로드 또는 플레이스홀더 표시
- ✅ 프로젝트 더블클릭 또는 OK 버튼으로 선택
- ✅ Cancel 버튼으로 앱 종료
- ✅ 선택한 프로젝트로 Context 자동 업데이트

### 에러 처리

- ✅ Shotgun 연결 실패 시 에러 메시지 표시
- ✅ 프로젝트 없음 시 경고 메시지 표시
- ✅ 썸네일 다운로드 실패 시 플레이스홀더로 대체
- ✅ 사용자 취소 시 정상 종료

## 🚀 사용 방법

```bash
# 1. Shotgun API 키 설정
export SHOTGUN_API_KEY="your-api-key-here"

# 2. 앱 실행 (프로젝트 선택 다이얼로그 자동 표시)
python app.py --no-rez

# 3. 프로젝트 선택 → 메인 UI 표시
```

## 📊 테스트 결과

```bash
$ python test_imports.py
============================================================
Import Test
============================================================
Qt binding: PyQt5 5.9.7

[1] Testing qt_compat imports...
✓ qt_compat imports successful

[2] Testing thumbnail_loader imports...
✓ thumbnail_loader imports successful

[3] Testing project_selector imports...
✓ project_selector imports successful

[4] Testing AppInstance.update_project_context...
✓ AppInstance.update_project_context exists

[5] Testing placeholder creation...
✓ Placeholder creation successful
  - Size: 240x144

[6] Testing initials extraction...
✓ Initials extraction successful
  - 'Westworld' -> 'W'
  - 'The Matrix' -> 'TM'
  - 'Star Wars Episode IV' -> 'SWE'
  - '' -> '?'

============================================================
All tests passed! ✓
============================================================
```

## 📂 파일 구조

```
tk-iomanager/
├── app.py                                 # [수정] 프로젝트 선택 통합
├── python/
│   └── app/
│       ├── __init__.py                   # [수정] update_project_context()
│       ├── ui/
│       │   └── project_selector.py      # [신규] 프로젝트 선택 다이얼로그
│       └── utils/
│           ├── qt_compat.py             # [수정] QListWidgetItem 추가
│           └── thumbnail_loader.py      # [신규] 썸네일 로더
├── test_imports.py                       # [신규] 임포트 테스트
└── test_project_selector.py             # [신규] UI 테스트
```

## 🔄 실행 흐름

```
app.py 실행
    ↓
설정 로드 (settings.yml)
    ↓
Shotgun API 초기화
    ↓
QApplication 생성
    ↓
프로젝트 선택 다이얼로그 표시 ← [NEW]
    ↓
사용자가 프로젝트 선택
    ↓
Context 업데이트 (project_id, name) ← [NEW]
    ↓
메인 다이얼로그 표시
    ↓
이벤트 루프 실행
```

## 📝 코드 예제

### 프로젝트 선택

```python
from python.app.ui.project_selector import show_project_selector
from python.app import get_shotgun

# Shotgun API 인스턴스
shotgun = get_shotgun()

# 프로젝트 선택 다이얼로그 표시
selected_project = show_project_selector(shotgun)

if selected_project:
    print(f"Selected: {selected_project['name']}")
else:
    print("Cancelled")
```

### Context 업데이트

```python
from python.app import AppInstance

# 프로젝트 선택 후
project = {
    'type': 'Project',
    'id': 123,
    'name': 'Westworld'
}

# Context 업데이트
AppInstance.update_project_context(project)

# Context 확인
context = AppInstance.get_context()
print(context.project)  # {'type': 'Project', 'id': 123, 'name': 'Westworld'}
```

## 🔧 설정

### `config/settings.yml`

```yaml
shotgun:
  base_url: "https://west.shotgunstudio.com"
  script_name: "westworld_util"
  script_key: "${SHOTGUN_API_KEY}"  # 환경변수 사용

context:
  project_id: 123  # [주의] 프로젝트 선택 시 무시됨 (런타임 업데이트)
  user: "${USER}"
```

## 💡 핵심 개선 사항

### 이전 방식 (settings.yml)
```yaml
context:
  project_id: 123  # 하드코딩, 프로젝트 변경 시 파일 수정 필요
```

### 새로운 방식 (프로젝트 선택)
```python
# 앱 시작 시 자동으로 프로젝트 선택 UI 표시
# 사용자가 프로젝트 선택 → Context 자동 업데이트
# 설정 파일 수정 불필요
```

## 🎨 UI 스크린샷 (Mock)

```
┌──────────────────────────────────────────────────────────┐
│  Select Project                                      [×] │
├──────────────────────────────────────────────────────────┤
│  Select a project to continue:                           │
│                                                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │
│  │   W     │  │   TM    │  │   SW    │                 │
│  │         │  │         │  │         │                 │
│  └─────────┘  └─────────┘  └─────────┘                 │
│  Westworld    The Matrix   Star Wars                    │
│                                                           │
│  ┌─────────┐                                            │
│  │  BR2049 │                                            │
│  │         │                                            │
│  └─────────┘                                            │
│  Blade Runner 2049                                      │
│                                                           │
│                                        [  OK  ] [Cancel] │
└──────────────────────────────────────────────────────────┘
```

## 📦 의존성

### 필수
- Python 2.7+ / 3.6+
- PyQt5 / PySide2 / PySide6 / PyQt6
- shotgun_api3

### 선택적
- requests (썸네일 다운로드용, 없으면 플레이스홀더만 표시)

## 🐛 알려진 제한사항

1. **동기 썸네일 다운로드**: 프로젝트 많으면 로딩 시간 증가
2. **프로젝트 선택 필수**: Cancel 누르면 앱 종료
3. **Shotgun 연결 필수**: 오프라인 모드 미지원

## 🔮 향후 개선 계획

- [ ] 비동기 썸네일 로딩 (QThread)
- [ ] 최근 프로젝트 기억 (JSON 파일)
- [ ] 프로젝트 검색 필터 (QLineEdit)
- [ ] 프로젝트 정렬 옵션 (Name/Recent/Code)
- [ ] 오프라인 모드 (settings.yml 폴백)

## 📚 관련 문서

- [PROJECT_SELECTOR_IMPLEMENTATION.md](./PROJECT_SELECTOR_IMPLEMENTATION.md) - 상세 구현 문서
- [config/settings.yml](./config/settings.yml) - 설정 파일

## ✨ 구현 완료

모든 Phase가 성공적으로 구현되었습니다!

- ✅ Phase 1: 프로젝트 선택 다이얼로그 생성
- ✅ Phase 2: 썸네일 다운로드 및 플레이스홀더
- ✅ Phase 3: 앱 시작 흐름 통합
- ✅ Phase 4: Context 업데이트 메서드
- ✅ Phase 5: 에러 처리
- ✅ 테스트 및 검증

**구현 일자**: 2026-02-11
**테스트 상태**: ✅ PASS
**프로덕션 준비**: ✅ READY
