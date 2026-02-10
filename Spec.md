# Flow(Shotgrid) Desktop 애플리케이션 개선 실행 계획

## Context

이 프로젝트는 Shotgun Toolkit(현재 Flow) 기반의 "Westworld IO-Manager" 애플리케이션으로, shot/source 파일을 등록하고 관리하는 VFX 파이프라인 도구입니다. 현재 Shotgun Toolkit 엔진에 강하게 의존하고 있어 독립 실행이 불가능하며, Python 2 코드베이스로 인한 호환성 문제와 성능/보안 이슈가 존재합니다.

세 가지 주요 개선 사항을 순차적으로 진행하여 애플리케이션의 독립성, 안정성, 유지보수성을 향상시키는 것이 목표입니다.

---

## 개선 사항 1: 독립 실행 가능한 애플리케이션으로 전환

### 목적
Shotgun Toolkit 엔진 의존성을 제거하고 독립적으로 실행 가능한 Python 애플리케이션으로 변환

### 현재 상태 분석

**SGTK 의존성 파일 및 라인:**
- `app.py:55,59,75,84` - Application 클래스 상속, 모듈 로드, 커맨드 등록
- `dialog.py:11,19,56,77,79,175` - 전체 파일에서 sgtk API 사용
- `publish.py:6,10,203,548,1070,1073` - 2007줄 중 다수 위치에서 SGTK 의존
- `collect.py:3,5,85-88,187,284` - 컨텍스트 및 Shotgun API 접근
- `validate.py:4,5,37-39` - 앱 인스턴스 및 Shotgun API 접근
- `sg_cmd.py:4,89,125,135,173` - SGTK Context 및 publish 등록
- 모든 UI 파일 - `sgtk.platform.qt` 또는 `tank.platform.qt` 사용

**주요 제거 대상:**
- `sgtk.platform.Application` 기본 클래스
- `sgtk.platform.current_bundle()` (15회 이상 사용)
- `sgtk.platform.qt` Qt 임포트 래퍼
- `sgtk.Context()`, `sgtk.util.register_publish()`
- `self.engine.register_command()`, `self.engine.show_dialog()`

### 실행 계획

#### Phase 1: 기반 Infrastructure 구축 (4-6시간)

**1.1 설정 관리 시스템 생성**
- 새 파일: `config/app_config.py`
  - `AppConfig` 클래스 생성 (Shotgun URL, API 키, 프로젝트 경로 등)
  - YAML 파일 로딩 기능 (`config/settings.yml`)
- 새 파일: `config/settings.yml`
  ```yaml
  shotgun:
    base_url: "https://west.shotgunstudio.com"
    script_name: "westworld_util"
    script_key: "${SHOTGUN_API_KEY}"  # 환경변수 사용
  project:
    path: "${PROJECT_ROOT}"
    name: "Westworld"
  context:
    project_id: 123
    user: "${USER}"
  ```

**1.2 Qt 호환성 레이어 생성**
- 새 파일: `python/app/utils/qt_compat.py`
  - PyQt5/PySide2 자동 선택 로직
  - QtCore, QtGui, QtWidgets 통합 임포트
  - 기존 `from sgtk.platform.qt` 모두 이것으로 교체

**1.3 글로벌 앱 인스턴스 관리**
- 수정: `python/app/__init__.py`
  - 싱글톤 패턴으로 `AppInstance` 클래스 생성
  - Shotgun API 인스턴스 관리 (`shotgun_api3` 직접 사용)
  - `sgtk.platform.current_bundle()` 대체

#### Phase 2: 메인 애플리케이션 변환 (3-4시간)

**2.1 app.py 재구성**
- 파일: `app.py`
  - `StgkStarterApp(Application)` → `IOManagerApp` 클래스로 변경
  - `init_app()` → `run()` 메서드로 변경
  - `self.import_module()` → 표준 `import` 사용
  - `self.engine.register_command()` 제거
  - CLI 인터페이스 추가 (argparse 사용)
  ```python
  if __name__ == "__main__":
      parser = argparse.ArgumentParser()
      parser.add_argument("--config", default="config/settings.yml")
      args = parser.parse_args()
      app = IOManagerApp(args.config)
      app.run()
  ```

**2.2 dialog.py 의존성 제거**
- 파일: `python/app/dialog.py:19,39,56,77,79,175,251`
  - `from sgtk.platform.qt` → `from python.app.utils.qt_compat`
  - `sgtk.platform.current_bundle()` → `AppInstance.get()`
  - `self.engine.show_dialog()` → `self.show()` (표준 Qt)
  - `self._app.context` → `AppConfig.get_context()`
  - `self._app.sgtk.shotgun` → `AppInstance.get_shotgun()`
  - `self._app.sgtk.project_path` → `AppConfig.get_project_path()`

**2.3 UI 파일 업데이트**
- 파일: `python/app/ui/dialog.py:10`
  - `from tank.platform.qt` → `from python.app.utils.qt_compat`

#### Phase 3: API 모듈 변환 (6-8시간)

**3.1 sg_cmd.py 변환**
- 파일: `python/app/api/sg_cmd.py:4,89,125,135,173`
  - `sgtk.Context()` → 간단한 `Context` 데이터 클래스 생성
  - `sgtk.util.register_publish()` → `shotgun_api3`로 직접 구현
    ```python
    published_file_data = {
        "project": project,
        "code": name,
        "path": {"local_path": path},
        "published_file_type": published_file_type,
        "version_number": version,
        "created_by": user
    }
    sg.create("PublishedFile", published_file_data)
    ```

**3.2 publish.py 대규모 변환**
- 파일: `python/app/api/publish.py` (2007줄, 40% SGTK 의존)
  - `sgtk.platform.qt` → `qt_compat`로 변경 (라인 10)
  - `sgtk.platform.current_bundle()` 모두 제거 (라인 203, 1070)
  - `app.sgtk.shotgun` → `AppInstance.get_shotgun()` (라인 1073)
  - `app.sgtk.project_path` → `AppConfig.get_project_path()` (라인 548)
  - 생성된 스크립트에서도 SGTK 참조 제거

**3.3 collect.py 변환**
- 파일: `python/app/api/collect.py:3,5,85-88,187,284`
  - `sgtk.platform.current_bundle()` 3회 제거
  - `app.shotgun`, `app.context` → 글로벌 인스턴스 사용

**3.4 validate.py 변환**
- 파일: `python/app/api/validate.py:4,5,37-39`
  - `sgtk.platform.current_bundle()` 제거
  - 유사한 패턴으로 변환

**3.5 기타 파일**
- `python/app/api/excel.py:12` - Qt 임포트만 변경
- `python/app/model/*.py` - Qt 임포트만 변경

#### Phase 4: Rez 패키지 관리 처리 (2-3시간)

**4.1 Rez 의존성 선택적 처리**
- 파일: `app.py:40-52`
  - Rez가 없는 환경에서도 실행 가능하도록 try-except 추가
  - 필수 패키지들 requirements.txt로 관리
  ```python
  try:
      from rez.resolved_context import ResolvedContext
      context = ResolvedContext(['tractor', 'pyseq', ...])
      # Rez 환경 설정
  except ImportError:
      # 일반 pip 패키지 사용
      pass
  ```

#### Phase 5: 테스트 및 검증 (3-4시간)

**5.1 단위 테스트 작성**
- 새 디렉토리: `tests/`
  - `test_app_config.py` - 설정 로딩 테스트
  - `test_qt_compat.py` - Qt 호환성 테스트
  - `test_sg_cmd.py` - Shotgun 연결 테스트

**5.2 통합 테스트**
- UI 초기화 및 표시 테스트
- Excel 생성 워크플로우 테스트
- Shotgun 연결 및 쿼리 테스트

**5.3 독립 실행 검증**
```bash
# Shotgun Toolkit 없이 실행
python app.py --config config/settings.yml
```

### 주요 파일 변경 요약

| 파일 | 라인 수 | SGTK 의존도 | 예상 작업 시간 |
|------|---------|------------|--------------|
| `app.py` | 89 | 100% | 3-4시간 |
| `python/app/dialog.py` | 293 | 70% | 2-3시간 |
| `python/app/api/publish.py` | 2007 | 40% | 4-6시간 |
| `python/app/api/sg_cmd.py` | 174 | 60% | 2-3시간 |
| `python/app/api/collect.py` | 366 | 35% | 2-3시간 |
| `python/app/api/validate.py` | 238 | 25% | 1-2시간 |
| 기타 파일들 | - | 5-10% | 2-3시간 |

**총 예상 시간: 18-28시간**

### 검증 방법
1. SGTK 없이 애플리케이션 실행 성공
2. Shotgun API 연결 및 쿼리 정상 작동
3. UI 초기화 및 모든 위젯 정상 표시
4. Excel 생성 기능 정상 작동
5. 기존 기능과 동일한 결과 출력

---

## 개선 사항 2: 썸네일 생성 및 엑셀 파일 생성 기능 개선

### 목적
Python 3 호환성 확보, 성능 개선, 에러 처리 강화, 코드 품질 향상

### 현재 상태 분석

**주요 문제점:**
1. **Python 2 코드** - `has_key()`, `dict.values()[:]`, `string.uppercase` 사용
2. **리소스 관리 미흡** - 파일 핸들 누수, context manager 미사용
3. **에러 처리 부족** - 예외 처리 없음, 로깅 부족
4. **성능 이슈** - 동기식 처리, ffmpeg.probe() 중복 호출
5. **하드코딩** - 썸네일 해상도 960x540 고정

**핵심 파일:**
- `python/app/api/excel.py` (714줄) - 메인 로직
- `python/app/api/collect.py` (366줄) - Nuke 스크립트 생성
- `python/app/api/validate.py` (238줄) - 검증 로직

### 실행 계획

#### Phase 1: Python 3 호환성 수정 (2-3시간)

**1.1 dict.has_key() 제거**
- 파일: `python/app/api/excel.py:73,155,330,344`
  ```python
  # Before
  if video_stream.has_key('tags'):

  # After
  if 'tags' in video_stream:
  ```

**1.2 dict.values() 리스트 변환**
- 파일: `python/app/api/excel.py:643`
  ```python
  # Before
  items = MODEL_KEYS.values()[1:]

  # After
  items = list(MODEL_KEYS.values())[1:]
  ```

**1.3 filter() 리스트 변환**
- 파일: `python/app/api/excel.py:553`
  ```python
  # Before
  excel_list = filter(lambda x: x.startswith('scanlist'), os.listdir(excel_path))

  # After
  excel_list = list(filter(lambda x: x.startswith('scanlist'), os.listdir(excel_path)))
  ```

**1.4 string 모듈 업데이트**
- 파일: `python/app/api/excel.py:657`
  ```python
  # Before
  import string
  string.uppercase

  # After
  import string
  string.ascii_uppercase
  ```

#### Phase 2: 리소스 관리 개선 (2-3시간)

**2.1 파일 핸들링 Context Manager 사용**
- 파일: `python/app/api/excel.py:508,521`
  ```python
  # Before
  f = open(edl_file, 'r')
  dl = parser.parse(f)

  # After
  with open(edl_file, 'r') as f:
      dl = parser.parse(f)
  ```

**2.2 OpenEXR 리소스 관리**
- 파일: `python/app/api/excel.py:343-348`
  ```python
  try:
      exr = OpenEXR.InputFile(exr_file)
      header = exr.header()
      # ... 처리
  finally:
      if exr:
          exr.close()  # 명시적 close (OpenEXR은 context manager 미지원)
  ```

**2.3 Workbook 리소스 관리**
- 파일: `python/app/api/excel.py:535-689`
  ```python
  def __enter__(self):
      return self

  def __exit__(self, exc_type, exc_val, exc_tb):
      self.wWorkbook.close()

  # 사용:
  with ExcelWriteModel(excel_path) as writer:
      writer.write_model_to_excel(model)
  ```

#### Phase 3: 에러 처리 및 로깅 강화 (3-4시간)

**3.1 로깅 시스템 도입**
- 새 파일: `python/app/utils/logger.py`
  ```python
  import logging

  def get_logger(name):
      logger = logging.getLogger(name)
      logger.setLevel(logging.INFO)
      handler = logging.FileHandler('iomanager.log')
      formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
      handler.setFormatter(formatter)
      logger.addHandler(handler)
      return logger
  ```

**3.2 FFmpeg 에러 처리**
- 파일: `python/app/api/excel.py:61-68,149-191`
  ```python
  # Before
  video_stream = ffmpeg.probe(mov_file)['streams'][0]

  # After
  try:
      probe_result = ffmpeg.probe(mov_file)
      video_stream = probe_result['streams'][0]
  except ffmpeg.Error as e:
      logger.error(f"FFmpeg probe failed for {mov_file}: {e.stderr}")
      return None
  except (KeyError, IndexError) as e:
      logger.error(f"Invalid video stream in {mov_file}: {e}")
      return None
  ```

**3.3 썸네일 생성 에러 처리**
- 파일: `python/app/api/excel.py:149-191`
  ```python
  # os.system() → subprocess.run()으로 변경
  import subprocess

  try:
      result = subprocess.run(command, capture_output=True, text=True, check=True)
      logger.info(f"Thumbnail created: {thumbnail_file}")
  except subprocess.CalledProcessError as e:
      logger.error(f"Thumbnail generation failed: {e.stderr}")
      raise
  ```

**3.4 Excel 쓰기 에러 처리**
- 파일: `python/app/api/excel.py:637-641`
  ```python
  try:
      self.wWorksheet.insert_image(row+1, col, data,
                                   {'x_scale': 0.25, 'y_scale': 0.25})
  except Exception as e:
      logger.warning(f"Failed to insert image at row {row}, col {col}: {e}")
      # 이미지 삽입 실패해도 계속 진행
  ```

#### Phase 4: 성능 최적화 (4-5시간)

**4.1 메타데이터 캐싱**
- 파일: `python/app/api/excel.py` - MOV_INFO 클래스 수정
  ```python
  class MOV_INFO(object):
      _probe_cache = {}  # 클래스 레벨 캐시

      @property
      def video_stream(self):
          if self._mov_file in self._probe_cache:
              return self._probe_cache[self._mov_file]

          stream = ffmpeg.probe(self._mov_file)['streams'][0]
          self._probe_cache[self._mov_file] = stream
          return stream
  ```

**4.2 배치 썸네일 생성**
- 파일: `python/app/api/excel.py:149-191`
  - 현재: MOV 파일당 개별 ffmpeg 실행
  - 개선: 동일 MOV 내 여러 프레임을 한 번에 처리 (이미 구현됨, 검증 필요)

**4.3 비동기 처리 도입 (선택사항)**
- 썸네일 생성을 별도 스레드에서 실행
  ```python
  from concurrent.futures import ThreadPoolExecutor

  def create_thumbnails_async(mov_list):
      with ThreadPoolExecutor(max_workers=4) as executor:
          futures = [executor.submit(_create_thumbnail_for_mov, mov)
                    for mov in mov_list]
          results = [f.result() for f in futures]
      return results
  ```

#### Phase 5: 유연성 개선 (2-3시간)

**5.1 설정 가능한 썸네일 해상도**
- 파일: `config/settings.yml`
  ```yaml
  thumbnail:
    width: 960
    height: 540
    quality: 90
  ```
- 적용: `python/app/api/excel.py:186,296`

**5.2 코덱 설정 외부화**
- 파일: `config/settings.yml`
  ```yaml
  codecs:
    "Apple ProRes 4444": "ap4h"
    "Apple ProRes 422 HQ": "apch"
    # ...
  ```
- 적용: `python/app/api/collect.py:39-50`

**5.3 컬러스페이스 설정 관리**
- 파일: `python/app/api/constant.py:35-59`
  - YAML로 이동하여 프로젝트별 커스터마이징 가능

#### Phase 6: 코드 품질 개선 (2-3시간)

**6.1 함수 분리 및 리팩토링**
- `_create_seq_array()` (45줄) - 각 메타데이터 추출을 독립 함수로
- `create_mov_nuke_script()` (95줄) - Natron/Nuke 부분을 별도 메서드로

**6.2 타입 힌팅 추가**
```python
from typing import List, Dict, Optional

def _get_sequences(path: str) -> List[pyseq.Sequence]:
    ...

def _get_resolution(seq: pyseq.Sequence) -> str:
    ...
```

**6.3 Docstring 추가**
```python
def create_excel(path: str) -> List[List]:
    """
    지정된 경로에서 시퀀스를 수집하고 엑셀용 배열을 생성합니다.

    Args:
        path: 스캔 파일이 있는 디렉토리 경로

    Returns:
        MODEL_KEYS 순서에 맞춘 2D 배열

    Raises:
        IOError: 경로가 존재하지 않을 때
    """
```

### 주요 변경 파일 요약

| 파일 | 개선 항목 | 예상 작업 시간 |
|------|---------|--------------|
| `excel.py` | Python 3, 리소스 관리, 에러 처리, 성능 | 8-10시간 |
| `collect.py` | Python 3, 에러 처리, 설정 외부화 | 3-4시간 |
| `validate.py` | Python 3, 에러 처리 | 2-3시간 |
| `constant.py` | 설정 외부화 | 1시간 |

**총 예상 시간: 15-21시간**

### 검증 방법
1. Python 3.7+ 환경에서 모든 기능 정상 작동
2. 대용량 파일(100+ 시퀀스)로 성능 테스트
3. 잘못된 파일 경로, 손상된 파일 등 에러 케이스 테스트
4. 로그 파일에 모든 작업 기록 확인
5. 메모리 누수 테스트 (장시간 실행)

---

## 개선 사항 3: Remote Job(RMS 서버용) 생성 개선

### 목적
설정 파일 기반 관리, 보안 강화, 에러 처리 개선, 유지보수성 향상

### 현재 상태 분석

**주요 문제점:**
1. **하드코딩된 RMS 호스트** - `10.0.20.81` (publish.py:1040)
2. **노출된 API 키** - Shotgun API 키가 소스코드에 평문 저장 (publish.py:1726)
3. **에러 처리 부족** - Job 실패 시 추적 어려움
4. **복잡한 조건문** - 컬러스페이스 처리 로직 중복 (publish.py:359-401, 741-770)
5. **Task 의존성 불명확** - addChild() 사용이 산재

**핵심 파일:**
- `python/app/api/publish.py` (2007줄) - 메인 Job 생성 로직
- `python/app/api/collect.py` (366줄) - Collect용 Tractor Job
- `python/app/api/validate.py` (238줄) - 검증 로직

### 실행 계획

#### Phase 1: 설정 파일 기반 구조 변경 (3-4시간)

**1.1 RMS/Tractor 설정 외부화**
- 파일: `config/settings.yml` (추가)
  ```yaml
  tractor:
    hostname: "10.0.20.81"
    default_priority: 10
    services:
      linux: "Linux64"
      lib: "lib"

  job_settings:
    title_prefix: "[IOM]"
    temp_cleanup: true
    max_retries: 3
  ```

**1.2 설정 로더 구현**
- 파일: `python/app/api/publish.py:1038-1041`
  ```python
  # Before
  self.job.spool(hostname="10.0.20.81", owner=user)

  # After
  from config.app_config import AppConfig
  config = AppConfig.get()
  self.job.spool(
      hostname=config.get('tractor.hostname'),
      owner=user
  )
  ```

**1.3 Job 기본 설정 적용**
- 파일: `python/app/api/publish.py:294-301`
  ```python
  def create_job(self):
      config = AppConfig.get()
      self.job = author.Job()
      self.job.title = config.get('job_settings.title_prefix') + self.shot_name + " publish"

      if self.seq_type == "lib":
          self.job.service = config.get('tractor.services.lib')
      else:
          self.job.service = config.get('tractor.services.linux')

      self.job.priority = config.get('tractor.default_priority', 10)
  ```

#### Phase 2: 보안 강화 (2-3시간)

**2.1 API 키 환경변수 처리**
- 파일: `python/app/api/publish.py:1722-1811` (create_sg_script 함수)
  ```python
  # Before (라인 1726-1728)
  nk += 'script_name = "westworld_util"\n'
  nk += 'script_key = "yctqnqdjd0bttz)ornewKuitt"\n'

  # After
  import os
  nk += 'import os\n'
  nk += 'script_name = os.environ.get("SHOTGUN_SCRIPT_NAME")\n'
  nk += 'script_key = os.environ.get("SHOTGUN_API_KEY")\n'
  nk += 'if not script_name or not script_key:\n'
  nk += '    raise EnvironmentError("Shotgun credentials not found in environment")\n'
  ```

**2.2 Shotgun URL 설정화**
- 파일: `config/settings.yml`
  ```yaml
  shotgun:
    base_url: "https://west.shotgunstudio.com"
    script_name_env: "SHOTGUN_SCRIPT_NAME"
    api_key_env: "SHOTGUN_API_KEY"
  ```

**2.3 생성 스크립트 보안 검증**
- 파일: `python/app/api/publish.py`
  - 모든 생성 스크립트에서 환경변수 사용
  - 로그에 API 키 노출 방지 (logger 필터 추가)

#### Phase 3: 에러 처리 강화 (4-5시간)

**3.1 Task 실행 에러 처리**
- 새 파일: `python/app/api/job_utils.py`
  ```python
  from tractor.api import author
  import logging

  logger = logging.getLogger(__name__)

  class TaskWithErrorHandling(author.Task):
      def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self.resumable = True  # 실패 시 재시도 가능
          self.retryrc = [1, 2, 3]  # 재시도할 리턴 코드

      def addCommand(self, command):
          # 에러 로깅을 위한 래퍼 추가
          wrapped_cmd = author.Command(
              argv=['bash', '-c', f'{" ".join(command.argv)} || (echo "Task failed" >&2; exit 1)']
          )
          super().addCommand(wrapped_cmd)
  ```

**3.2 Job 제출 전 검증**
- 파일: `python/app/api/publish.py:1038-1041` (submit_job 함수)
  ```python
  def submit_job(self):
      # 제출 전 검증
      if not self._validate_job():
          raise ValueError("Job validation failed")

      try:
          user = os.environ.get('USER', 'unknown')
          config = AppConfig.get()
          hostname = config.get('tractor.hostname')

          logger.info(f"Submitting job '{self.job.title}' to {hostname}")
          self.job.spool(hostname=hostname, owner=user)
          logger.info(f"Job submitted successfully: {self.job.title}")

      except Exception as e:
          logger.error(f"Job submission failed: {e}")
          raise

  def _validate_job(self):
      """Job 제출 전 검증"""
      # 필수 파일 존재 확인
      if self.nuke_script and not os.path.exists(self.nuke_script):
          logger.error(f"Nuke script not found: {self.nuke_script}")
          return False

      # 출력 경로 쓰기 권한 확인
      if not os.access(self.plate_path, os.W_OK):
          logger.error(f"No write permission: {self.plate_path}")
          return False

      return True
  ```

**3.3 Nuke 스크립트 실행 에러 처리**
- 파일: `python/app/api/publish.py` - 모든 create_*_job 함수
  ```python
  # 각 Task에 에러 처리 추가
  cmd = ['rez-env', 'nuke-12', '--', 'nuke', '-ix', self.nuke_script]
  cmd_with_error = cmd + ['||', 'echo', '"Nuke execution failed"', '>&2']
  ```

#### Phase 4: 코드 구조 개선 (4-5시간)

**4.1 컬러스페이스 로직 리팩토링**
- 파일: `python/app/api/publish.py:359-401, 741-770`
  ```python
  # Before: 중복된 if-elif 체인

  # After: 딕셔너리 기반 매핑
  class ColorspaceManager:
      COLORSPACE_SETTINGS = {
          "ACES": {
              "rez_packages": ['nuke-12', 'ocio_config'],
              "read_colorspace": "ACES - ACEScg",
              "write_colorspace": "Output - Rec.709"
          },
          "AlexaV3LogC": {
              "rez_packages": ['nuke-12', 'alexa_config'],
              "read_colorspace": "AlexaV3LogC",
              "write_colorspace": "Output - Rec.709"
          },
          # ... 다른 컬러스페이스들
      }

      @classmethod
      def get_nuke_command(cls, colorspace, script_path):
          settings = cls._get_settings(colorspace)
          cmd = ['rez-env'] + settings['rez_packages'] + ['--', 'nuke', '-ix', script_path]
          return cmd

      @classmethod
      def _get_settings(cls, colorspace):
          for key, settings in cls.COLORSPACE_SETTINGS.items():
              if colorspace.find(key) != -1:
                  return settings
          return cls.COLORSPACE_SETTINGS.get("default")
  ```

**4.2 Task 의존성 명확화**
- 파일: `python/app/api/publish.py`
  ```python
  class JobBuilder:
      """Tractor Job 빌더 클래스"""

      def __init__(self, master_input, seq_type):
          self.job = author.Job()
          self.tasks = {}
          # ... 초기화

      def build(self):
          """전체 Job 구성"""
          self._create_base_job()
          self._add_tasks()
          self._setup_dependencies()
          return self.job

      def _add_tasks(self):
          """모든 Task 추가"""
          self.tasks['temp'] = self._create_temp_task()
          self.tasks['jpg'] = self._create_jpg_task()
          self.tasks['org'] = self._create_org_task()
          # ...

      def _setup_dependencies(self):
          """Task 의존성 설정"""
          # 명확한 의존성 체인
          dependencies = [
              ('jpg', 'org'),   # org는 jpg 이후
              ('jpg', 'copy'),  # copy는 jpg 이후
              ('sg', 'mp4'),    # mp4는 sg 이후
          ]

          for parent, child in dependencies:
              if parent in self.tasks and child in self.tasks:
                  self.tasks[parent].addChild(self.tasks[child])
                  logger.debug(f"Dependency: {parent} -> {child}")
  ```

**4.3 스크립트 생성 로직 분리**
- 새 파일: `python/app/api/script_generators/`
  - `nuke_script_generator.py` - Nuke 스크립트 생성
  - `natron_script_generator.py` - Natron 스크립트 생성
  - `shotgun_script_generator.py` - Shotgun 업로드 스크립트

  각 제너레이터는 템플릿 기반으로 스크립트 생성

#### Phase 5: 모니터링 및 로깅 (2-3시간)

**5.1 Job 상태 추적**
- 새 파일: `python/app/api/job_monitor.py`
  ```python
  class JobMonitor:
      """Tractor Job 상태 모니터링"""

      def __init__(self, job_id):
          self.job_id = job_id

      def get_status(self):
          """Tractor API로 Job 상태 조회"""
          # Tractor Query API 사용
          pass

      def wait_for_completion(self, timeout=3600):
          """Job 완료 대기"""
          pass

      def get_failed_tasks(self):
          """실패한 Task 목록 반환"""
          pass
  ```

**5.2 상세 로깅**
- 파일: `python/app/api/publish.py`
  ```python
  logger = get_logger('publish')

  def create_job(self):
      logger.info("=" * 50)
      logger.info(f"Creating job for shot: {self.shot_name}")
      logger.info(f"Seq type: {self.seq_type}")
      logger.info(f"Version: {self.version}")
      # ... Job 생성 로직
      logger.info(f"Job created: {self.job.title}")
      logger.debug(f"Job service: {self.job.service}")
      logger.debug(f"Job priority: {self.job.priority}")
  ```

#### Phase 6: 테스트 및 검증 (3-4시간)

**6.1 단위 테스트**
- 새 파일: `tests/test_publish.py`
  ```python
  import unittest
  from python.app.api.publish import Publish, ColorspaceManager

  class TestColorspaceManager(unittest.TestCase):
      def test_aces_colorspace(self):
          cmd = ColorspaceManager.get_nuke_command("ACES - ACEScg", "/tmp/test.nk")
          self.assertIn('ocio_config', cmd)

      # ... 더 많은 테스트
  ```

**6.2 통합 테스트**
- Job 생성 및 제출 시뮬레이션
- 실제 Tractor 서버에 테스트 Job 제출
- 로그 파일 검증

**6.3 보안 검증**
- 생성된 스크립트에 API 키 노출 여부 확인
- 환경변수 누락 시 에러 처리 확인

### 주요 변경 파일 요약

| 파일 | 개선 항목 | 예상 작업 시간 |
|------|---------|--------------|
| `publish.py` | 설정화, 보안, 에러 처리, 리팩토링 | 10-12시간 |
| `collect.py` | 설정화, 에러 처리 | 2-3시간 |
| `job_utils.py` (신규) | Task 래퍼, 에러 처리 | 2-3시간 |
| `script_generators/` (신규) | 스크립트 생성 분리 | 3-4시간 |
| `job_monitor.py` (신규) | Job 모니터링 | 2-3시간 |

**총 예상 시간: 18-25시간**

### 검증 방법
1. 설정 파일만 변경하여 다른 RMS 서버에 제출 가능
2. 환경변수 없이 실행 시 명확한 에러 메시지
3. Job 제출 실패 시 로그에 상세 정보 기록
4. 모든 Task의 의존성이 문서화됨
5. 테스트 Job을 실제 Tractor에 제출하여 정상 실행 확인

---

## 전체 프로젝트 타임라인

### 순차 진행 시 (권장)

| 단계 | 개선 사항 | 예상 시간 | 의존성 |
|------|---------|---------|--------|
| 1 | 독립 실행 가능 전환 | 18-28시간 | 없음 (먼저 진행) |
| 2 | 썸네일/엑셀 기능 개선 | 15-21시간 | 1단계 완료 후 (Python 3 필수) |
| 3 | Remote Job 개선 | 18-25시간 | 1단계 완료 후 (설정 시스템 필요) |

**총 예상 시간: 51-74시간 (약 6-9주, 주당 8시간 작업 기준)**

### 병렬 진행 시 (선택사항)

- **개선 사항 2와 3을 병렬 진행 가능** (독립 실행 전환 완료 후)
- 총 소요 시간: 약 33-49시간 (4-6주)

---

## 중요 고려 사항

### 1. 호환성 유지
- 기존 워크플로우와 데이터 포맷 호환성 유지
- 기존 Excel 파일 읽기 가능
- 기존 Shotgun 데이터 구조 유지

### 2. 점진적 배포
- 각 개선 사항을 독립적으로 배포 가능하도록 설계
- Feature flag 사용 고려
- 이전 버전으로 롤백 가능한 구조

### 3. 문서화
- 각 단계별 변경 사항 문서화
- 새로운 설정 파일 형식 문서화
- API 변경 사항 마이그레이션 가이드 작성

### 4. 테스트 전략
- 단위 테스트 커버리지 60% 이상 목표
- 통합 테스트로 전체 워크플로우 검증
- 실제 프로덕션 데이터로 회귀 테스트

### 5. 성능 목표
- Excel 생성 시간: 50% 단축 (100+ 시퀀스 기준)
- 썸네일 생성: 메모리 사용량 30% 감소
- Job 제출: 에러율 90% 감소

---

## 다음 단계

1. **우선순위 결정**: 개선 사항 1 → 2 → 3 순서로 진행 권장
2. **개발 환경 설정**: Python 3.7+, 필요한 라이브러리 설치
3. **Git 브랜치 전략**: feature/standalone, feature/excel-improvement, feature/rms-improvement
4. **코드 리뷰**: 각 Phase 완료 후 리뷰
5. **테스트 환경**: 별도 테스트 프로젝트에서 검증 후 프로덕션 적용

이 계획은 각 개선 사항을 독립적으로 진행할 수 있도록 설계되었으며, 필요에 따라 우선순위를 조정할 수 있습니다.
