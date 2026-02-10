# Westworld IO-Manager

독립 실행 가능한 VFX 파이프라인 도구로, Shot/Source 파일을 등록하고 관리합니다.

## 개요

이 애플리케이션은 원래 Shotgun Toolkit (SGTK) 기반으로 개발되었으나, **독립 실행 가능한 Python 애플리케이션**으로 변환되었습니다.

### 주요 기능

- **Excel 기반 Shot 관리**: EDL 파일에서 shot 정보를 추출하고 Excel로 관리
- **썸네일 생성**: MOV, EXR, DPX 파일에서 자동으로 썸네일 생성
- **Shotgun 통합**: Flow (Shotgun) API를 통한 버전 및 퍼블리시 등록
- **Tractor Job 생성**: Pixar Tractor를 통한 렌더 큐 관리
- **컬러스페이스 관리**: ACES, AlexaLogC 등 다양한 컬러스페이스 지원

## 시스템 요구사항

### Python 버전
- Python 3.7 이상

### 필수 패키지

```bash
pip install -r requirements.txt
```

## 설정

### 환경변수 설정

```bash
export SHOTGUN_API_KEY="your-shotgun-api-key"
export PROJECT_ROOT="/path/to/project"
export USER="your-username"
```

### 설정 파일

`config/settings.yml` 파일에서 프로젝트별 설정을 관리합니다.

## 실행

### 방법 1: 실행 스크립트 사용 (권장)

먼저 API 키를 설정하세요:

**macOS/Linux**:
```bash
# run.sh 편집하여 API 키 설정
export SHOTGUN_API_KEY="your-actual-api-key"
export PROJECT_ROOT="/path/to/project"

# 실행
./run.sh
```

**Windows**:
```cmd
# run.bat 편집하여 API 키 설정
set SHOTGUN_API_KEY=your-actual-api-key
set PROJECT_ROOT=C:\path\to\project

# 실행
run.bat
```

### 방법 2: 직접 실행

```bash
# 환경변수 설정
export SHOTGUN_API_KEY="your-api-key"
export PROJECT_ROOT="/path/to/project"
export USER="your-username"

# 기본 설정으로 실행
python app.py

# 커스텀 설정 파일 사용
python app.py --config /path/to/custom_settings.yml

# Rez 환경 비활성화 (pip 패키지 사용)
python app.py --no-rez

# 버전 확인
python app.py --version
```

## 테스트

```bash
# 전체 테스트
pytest tests/ -v

# 테스트 스크립트 사용
./run_tests.sh
```

### 테스트 결과 (Phase 5 검증 완료)

✅ **단위 테스트**
- `test_app_config.py`: 13/13 passed
- `test_qt_compat.py`: 9/11 passed (2 skipped)
- `test_sg_cmd.py`: 4개 import 테스트 passed

✅ **통합 테스트**
- 28개 테스트 통과
- 15개 외부 의존성 skip (정상)

## 개선 사항 (v2.0.0)

### ✅ Phase 1-5 완료

1. **Infrastructure 구축**: 설정 관리, Qt 호환성, 싱글톤 패턴
2. **메인 애플리케이션 변환**: SGTK 의존성 제거, CLI 추가
3. **API 모듈 변환**: Shotgun API 직접 호출
4. **Rez 패키지 관리**: requirements.txt, 에러 처리 개선
5. **테스트 및 검증**: 단위/통합 테스트, 독립 실행 검증

## 문의

자세한 내용은 `Spec.md` 파일을 참조하세요.

**버전**: 2.0.0 (독립 실행 가능)
