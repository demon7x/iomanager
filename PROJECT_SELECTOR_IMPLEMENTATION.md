# Shotgun 프로젝트 선택 UI 구현

## 개요

IO-Manager가 독립 실행 모드(--no-rez)로 시작할 때, Shotgun에서 프로젝트 목록을 썸네일 형태로 표시하고 사용자가 프로젝트를 선택할 수 있도록 하는 UI를 구현했습니다.

## 구현된 파일

### 1. `python/app/ui/project_selector.py` (신규)

프로젝트 선택 다이얼로그의 메인 구현 파일입니다.

**주요 클래스:**
- `ProjectSelectorDialog`: 프로젝트 선택 다이얼로그 (QDialog 상속)
  - QListWidget의 IconMode를 사용하여 그리드 레이아웃으로 프로젝트 표시
  - 썸네일 크기: 240x144
  - 그리드 크기: 280x220
  - 더블클릭 또는 OK 버튼으로 프로젝트 선택
  - Cancel 버튼으로 앱 종료

**주요 메서드:**
- `_load_projects()`: Shotgun에서 활성 프로젝트 조회
- `_add_project_item()`: 프로젝트 리스트 아이템 추가
- `_load_thumbnail()`: 프로젝트 썸네일 로드 (다운로드 또는 플레이스홀더)

**헬퍼 함수:**
- `show_project_selector(shotgun)`: 다이얼로그를 표시하고 선택된 프로젝트 반환

### 2. `python/app/utils/thumbnail_loader.py` (신규)

썸네일 다운로드 및 플레이스홀더 생성 유틸리티입니다.

**주요 함수:**
- `download_thumbnail(image_url, timeout=5)`: Shotgun 이미지 URL에서 썸네일 다운로드
  - requests 라이브러리 사용
  - 실패 시 None 반환
  - 성공 시 240x144 크기로 조정된 QPixmap 반환

- `create_placeholder(project_name, width=240, height=144)`: 플레이스홀더 생성
  - 짙은 회색 배경 (RGB: 60, 60, 60)
  - 프로젝트 이니셜 텍스트 오버레이 (최대 3글자)
  - 테두리 포함

- `_get_initials(project_name)`: 프로젝트 이름에서 이니셜 추출
  - 예: "Westworld" → "W", "The Matrix" → "TM"

### 3. `python/app/__init__.py` (수정)

**추가된 메서드:**
```python
@classmethod
def update_project_context(cls, project_dict):
    """
    런타임에 프로젝트 컨텍스트를 업데이트합니다.

    Args:
        project_dict: Shotgun 프로젝트 딕셔너리
                     {'type': 'Project', 'id': 123, 'name': 'ProjectName'}
    """
```

- Context가 없으면 생성
- 프로젝트 정보를 Context.project에 저장
- 로그 출력

### 4. `app.py` (수정)

**추가된 메서드:**
```python
def _handle_project_selection(self):
    """프로젝트 선택 처리"""
```

**동작:**
1. Shotgun API 인스턴스 획득
2. 연결 실패 시 에러 메시지 표시 후 종료
3. 프로젝트 선택 다이얼로그 표시
4. 사용자가 취소하면 앱 종료
5. 프로젝트 선택 시 Context 업데이트

**`run()` 메서드 수정:**
```python
def run(self):
    # QApplication 생성
    # ...

    # 프로젝트 선택 다이얼로그 표시 (신규)
    self._handle_project_selection()

    # 메인 다이얼로그 표시
    # ...
```

### 5. `python/app/utils/qt_compat.py` (수정)

**추가된 임포트:**
- `QListWidgetItem`: 리스트 위젯 아이템 클래스
- `QIcon`: 아이콘 클래스 (이미 있었으나 확인)
- `QFont`: 폰트 클래스 (이미 있었으나 확인)

## 실행 흐름

### 독립 실행 모드 (--no-rez)

```
app.py 실행
  ↓
IOManagerApp._initialize()
  - 설정 로드 (config/settings.yml)
  - AppInstance 초기화
  - Shotgun API 연결
  ↓
IOManagerApp.run()
  - QApplication 생성
  ↓
IOManagerApp._handle_project_selection()
  - Shotgun API 인스턴스 확인
  - 프로젝트 선택 다이얼로그 표시
  - 사용자가 프로젝트 선택
  - Context 업데이트
  ↓
메인 다이얼로그 표시
  - dialog.show_dialog()
  ↓
이벤트 루프 실행
```

## 테스트

### 테스트 파일

1. **`test_imports.py`**: 모든 새로운 모듈의 임포트 검증
   ```bash
   python test_imports.py
   ```

   **검증 항목:**
   - qt_compat 임포트
   - thumbnail_loader 임포트
   - project_selector 임포트
   - AppInstance.update_project_context 존재 확인
   - 플레이스홀더 생성 테스트
   - 이니셜 추출 테스트

2. **`test_project_selector.py`**: 프로젝트 선택 UI 테스트 (GUI)
   ```bash
   python test_project_selector.py
   ```

   **동작:**
   - Mock Shotgun API 사용 (실제 연결 불필요)
   - 4개의 테스트 프로젝트 표시
   - 사용자가 프로젝트 선택 또는 취소
   - 선택 결과 출력

### 테스트 결과

✓ 모든 임포트 테스트 통과
✓ 플레이스홀더 생성 성공 (240x144)
✓ 이니셜 추출 정상 동작

## 사용 방법

### 독립 실행 모드로 앱 시작

```bash
# 기본 실행 (프로젝트 선택 다이얼로그 표시)
python app.py --no-rez

# 커스텀 설정 파일 사용
python app.py --no-rez --config /path/to/settings.yml
```

### 환경변수 설정

```bash
# Shotgun API 키 설정 (필수)
export SHOTGUN_API_KEY="your-api-key-here"

# 프로젝트 루트 경로 (선택사항)
export PROJECT_ROOT="/path/to/project"
```

### 프로젝트 선택 흐름

1. **앱 시작**: `python app.py --no-rez`
2. **프로젝트 선택 다이얼로그 표시**
   - Shotgun에서 활성 프로젝트 로드
   - 썸네일 또는 플레이스홀더와 함께 그리드 표시
3. **프로젝트 선택**
   - 프로젝트 클릭 후 OK 버튼
   - 또는 프로젝트 더블클릭
4. **메인 다이얼로그 표시**
   - 선택한 프로젝트로 Context 설정
   - IO Manager 메인 UI 표시

### 취소 흐름

1. **Cancel 버튼 클릭** 또는 **다이얼로그 닫기 (X)**
2. **앱 종료**: 메시지 없이 정상 종료

## 에러 처리

### Shotgun 연결 실패

**증상:**
- `get_shotgun()` 반환값이 `None`
- Shotgun API 키 미설정 또는 잘못된 키

**동작:**
```
QMessageBox.critical()로 에러 메시지 표시:
"Failed to connect to Shotgun.
Please check your network and credentials in settings.yml"

sys.exit(1)로 앱 종료
```

### 프로젝트 없음

**증상:**
- Shotgun에서 활성 프로젝트가 없음
- `shotgun.find()` 결과가 빈 리스트

**동작:**
```
QMessageBox.warning()으로 경고 메시지 표시:
"No active projects found in Shotgun.
Please check your Shotgun configuration."

Cancel 버튼을 눌러 앱 종료 가능
```

### 썸네일 다운로드 실패

**증상:**
- 네트워크 오류
- 잘못된 이미지 URL
- requests 라이브러리 미설치

**동작:**
- 에러 로그 출력 (콘솔)
- 플레이스홀더로 대체
- 다른 프로젝트의 썸네일은 정상 표시

## 의존성

### 필수 라이브러리

```python
# Python 표준 라이브러리
import os
import sys
from typing import Optional, Dict, Any

# Qt (PyQt5, PySide2, PySide6, PyQt6 중 하나)
from PyQt5 import QtCore, QtGui, QtWidgets
# 또는
from PySide6 import QtCore, QtGui, QtWidgets

# Shotgun API
import shotgun_api3

# HTTP 요청 (썸네일 다운로드용)
import requests
```

### 선택적 라이브러리

- **requests**: 썸네일 다운로드에 필요
  - 미설치 시 플레이스홀더만 표시
  - 설치: `pip install requests`

## 설정 파일

### `config/settings.yml`

**Shotgun 설정:**
```yaml
shotgun:
  base_url: "https://west.shotgunstudio.com"
  script_name: "westworld_util"
  script_key: "${SHOTGUN_API_KEY}"  # 환경변수 사용
```

**컨텍스트 설정:**
```yaml
context:
  project_id: 123  # 프로젝트 선택 후 자동 업데이트됨 (미사용)
  user: "${USER}"
```

**주의:** `context.project_id`는 프로젝트 선택 다이얼로그 사용 시 무시됩니다. 런타임에 선택한 프로젝트 ID가 Context에 설정됩니다.

## 호환성

### Qt 버전

- **PyQt5**: 5.9.7+ (테스트 완료)
- **PySide2**: 지원
- **PySide6**: 지원
- **PyQt6**: 지원

### Python 버전

- **Python 2.7**: 지원 (레거시)
- **Python 3.6+**: 지원 (권장)

### Shotgun API

- **shotgun_api3**: 3.0.0+

## 커스터마이징

### 썸네일 크기 변경

**`project_selector.py`:**
```python
# 썸네일 크기
self.list_widget.setIconSize(QSize(240, 144))  # 변경 가능
self.list_widget.setGridSize(QSize(280, 220))  # 썸네일 + 여백
```

**`thumbnail_loader.py`:**
```python
def download_thumbnail(image_url, timeout=5):
    # ...
    pixmap = pixmap.scaled(240, 144, ...)  # 썸네일 크기와 동일하게
```

```python
def create_placeholder(project_name, width=240, height=144):
    # width, height 변경 가능
```

### 플레이스홀더 스타일 변경

**`thumbnail_loader.py`:**
```python
def create_placeholder(project_name, width=240, height=144):
    # 배경색
    pixmap.fill(QColor(60, 60, 60))  # RGB 값 변경

    # 텍스트 색상
    painter.setPen(QColor(180, 180, 180))  # RGB 값 변경

    # 폰트 크기
    font.setPixelSize(48)  # 픽셀 크기 변경
```

### 프로젝트 필터링

**`project_selector.py`:**
```python
def _load_projects(self):
    # 필터 변경
    filters = [
        ['archived', 'is', False],
        # 추가 필터 예:
        # ['name', 'contains', 'West'],  # 이름에 'West' 포함
        # ['sg_status', 'is', 'Active'],  # 상태가 Active
    ]
```

## 알려진 제한사항

1. **썸네일 다운로드 동기식**
   - 프로젝트 수가 많으면 로딩 시간 증가
   - 향후 QThread로 비동기 변환 가능

2. **프로젝트 선택 필수**
   - 프로젝트를 선택하지 않고 Cancel 누르면 앱 종료
   - settings.yml의 기본 프로젝트 폴백 없음

3. **Shotgun 연결 필수**
   - Shotgun API 연결 실패 시 앱 실행 불가
   - 오프라인 모드 미지원

## 향후 개선 사항

### 1. 비동기 썸네일 로딩

```python
class ThumbnailLoader(QThread):
    """비동기 썸네일 로더"""
    thumbnail_loaded = Signal(int, QPixmap)

    def run(self):
        # 썸네일 다운로드
        # Signal로 결과 전달
```

### 2. 최근 프로젝트 기억

```python
# ~/.claude/io-manager/recent_projects.json
{
    "last_project_id": 123,
    "recent_projects": [123, 456, 789]
}
```

### 3. 프로젝트 검색 필터

```python
# QLineEdit 추가
search_box = QLineEdit()
search_box.setPlaceholderText("Search projects...")
search_box.textChanged.connect(self._filter_projects)
```

### 4. 프로젝트 정렬 옵션

```python
# QComboBox 추가
sort_combo = QComboBox()
sort_combo.addItems(["Name", "Recent", "Code"])
sort_combo.currentTextChanged.connect(self._sort_projects)
```

## 문제 해결

### Q: "ImportError: cannot import name 'QListWidgetItem'"

**A:** `qt_compat.py`에 `QListWidgetItem`이 없습니다. 이미 수정됨.

### Q: "QPixmap: Must construct a QGuiApplication before a QPixmap"

**A:** `create_placeholder()` 호출 전에 `QApplication` 생성 필요.

### Q: "Failed to connect to Shotgun"

**A:**
1. `SHOTGUN_API_KEY` 환경변수 확인
2. `config/settings.yml`의 `shotgun.base_url` 확인
3. 네트워크 연결 확인

### Q: "No active projects found"

**A:**
1. Shotgun에 활성 프로젝트가 있는지 확인
2. `archived` 필드 확인 (False여야 함)
3. Shotgun 권한 확인 (프로젝트 읽기 권한)

## 참고 문서

- **Shotgun API**: https://developer.shotgridsoftware.com/python-api/
- **Qt Documentation**: https://doc.qt.io/
- **PyQt5 Tutorial**: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **PySide6 Tutorial**: https://doc.qt.io/qtforpython/

## 변경 이력

### 2026-02-11
- ✅ Phase 1: 프로젝트 선택 다이얼로그 생성
- ✅ Phase 2: 썸네일 다운로드 및 플레이스홀더 생성
- ✅ Phase 3: 앱 시작 흐름 통합
- ✅ Phase 4: Context 업데이트 메서드 추가
- ✅ Phase 5: 에러 처리 강화
- ✅ 테스트 스크립트 작성 및 검증 완료
