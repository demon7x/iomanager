# 설치 가이드

## Python 버전별 설치 방법

현재 시스템: **Python 3.9.12**

---

## 방법 1: PySide6 사용 (권장 - Python 3.9+)

```bash
# 1. 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는 Windows: venv\Scripts\activate

# 2. pip 업그레이드
pip install --upgrade pip

# 3. 의존성 설치
pip install -r requirements.txt
```

**requirements.txt는 기본적으로 PySide6를 사용합니다.**

---

## 방법 2: PyQt5 사용 (대안)

PyQt5를 사용하려면:

```bash
# 1. requirements.txt 수정
# PySide6>=6.0.0 라인을 주석 처리하고
# PyQt5>=5.15.0 라인의 주석을 해제

# 2. 설치
pip install PyQt5>=5.15.0
pip install -r requirements.txt  # 나머지 의존성
```

---

## 방법 3: PySide2 사용 (Python < 3.9)

Python 3.8 이하 버전에서는:

```bash
# 1. requirements.txt 수정
# PySide6>=6.0.0 라인을 주석 처리하고
# PySide2>=5.13.2,<5.14.0 라인의 주석을 해제

# 2. 설치
pip install PySide2==5.13.2
pip install -r requirements.txt
```

---

## 선택적 패키지 설치

### VFX 파이프라인 패키지

이 패키지들은 VFX 스튜디오 환경에서만 필요합니다:

```bash
# Option 1: 전체 VFX 패키지 설치
pip install -r requirements-vfx.txt

# Option 2: 수동으로 순서대로 설치 (권장)
pip install timecode                                    # 먼저 설치
pip install git+https://github.com/t-astein/python-edl # timecode 의존 (GitHub에서 설치 필요)
pip install pyseq                                       # 시퀀스 파일 처리
pip install pydpx-meta                                  # DPX 메타데이터 (C 컴파일러 필요)
```

**주의**:
- `edl` 패키지는 반드시 GitHub에서 설치해야 합니다 (PyPI 버전은 문제가 있음)
- `edl` 설치 전에 `timecode`를 먼저 설치해야 합니다
- `pydpx-meta`와 `OpenEXR`은 시스템 라이브러리가 필요할 수 있습니다

### Shotgun API

```bash
# GitHub에서 직접 설치
pip install git+https://github.com/shotgunsoftware/python-api.git@v3.3.6#egg=shotgun-api3
```

### OpenEXR

OpenEXR은 시스템 라이브러리가 필요할 수 있습니다:

**macOS (Homebrew)**:
```bash
brew install openexr
pip install OpenEXR
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install libopenexr-dev
pip install OpenEXR
```

**Windows**:
```bash
# 미리 빌드된 wheel 파일 사용
pip install OpenEXR
```

---

## 설치 확인

```bash
# Python 버전 확인
python --version

# Qt 바인딩 확인
python -c "from python.app.utils.qt_compat import get_qt_binding; print(get_qt_binding())"

# 예상 출력: PySide6 (또는 PyQt5, PySide2)

# 전체 테스트
pytest tests/test_qt_compat.py -v
```

---

## 트러블슈팅

### 1. PySide2 버전 에러

**에러**:
```
ERROR: No matching distribution found for PySide2>=5.15.0
```

**해결책**:
- Python 3.9 이상: PySide6 또는 PyQt5 사용
- Python 3.8 이하: PySide2==5.13.2 사용

### 2. OpenEXR 설치 실패

**에러**:
```
error: command 'gcc' failed with exit status 1
```

**해결책**:
1. 시스템에 OpenEXR 라이브러리 설치 (위 참조)
2. 또는 requirements.txt에서 OpenEXR 라인 주석 처리

### 3. Shotgun API 설치 실패

**해결책**:
```bash
# 수동으로 클론 후 설치
git clone https://github.com/shotgunsoftware/python-api.git
cd python-api
pip install -e .
```

---

## 최소 설치 (테스트만)

테스트만 실행하려면:

```bash
# 최소 의존성
pip install PyYAML
pip install PySide6  # 또는 PyQt5
pip install pytest
pip install pytest-qt

# 테스트 실행
pytest tests/test_app_config.py -v
pytest tests/test_qt_compat.py -v
```

---

## 완전 설치 (프로덕션)

모든 기능을 사용하려면:

```bash
# 1. Qt 바인딩
pip install PySide6>=6.0.0

# 2. 핵심 의존성
pip install PyYAML>=5.4.1
pip install Pillow>=8.0.0
pip install xlsxwriter>=3.0.0
pip install xlrd>=2.0.0

# 3. VFX 패키지
pip install pyseq>=0.7.0
pip install timecode>=1.3.0
pip install git+https://github.com/t-astein/python-edl  # GitHub에서 설치 필요

# 4. Shotgun
pip install git+https://github.com/shotgunsoftware/python-api.git@v3.3.6#egg=shotgun-api3

# 5. 테스트
pip install pytest>=6.0.0
pip install pytest-qt>=4.0.0
```

---

## 환경변수 설정

설치 후 환경변수를 설정하세요:

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가

export SHOTGUN_API_KEY="your-api-key-here"
export PROJECT_ROOT="/path/to/your/project"
export USER="your-username"
```

---

## 실행 확인

```bash
# 애플리케이션 버전 확인
python app.py --version

# 도움말
python app.py --help

# 테스트 실행
./run_tests.sh
```

예상 출력:
```
============================================================
Westworld IO-Manager
============================================================
Qt binding: PySide6 6.x.x
Loaded configuration from: config/settings.yml
✓ Rez environment ready
------------------------------------------------------------
Loading configuration from: config/settings.yml
Application initialized successfully
Using Qt binding: PySide6
```

---

## 다음 단계

설치가 완료되면:

1. `config/settings.yml` 파일 설정
2. 환경변수 확인
3. 테스트 실행으로 검증
4. 애플리케이션 실행

자세한 내용은 `README.md`를 참조하세요.
