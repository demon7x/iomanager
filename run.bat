@echo off
REM
REM IO Manager 실행 스크립트 (Windows)
REM
REM 사용법:
REM   run.bat
REM
REM 환경변수:
REM   SHOTGUN_API_KEY       Shotgun API 키 (필수)
REM   PROJECT_ROOT          프로젝트 루트 경로 (선택)
REM   USER                  사용자 이름 (선택, 기본값: 현재 사용자)

REM 스크립트 디렉토리로 이동
cd /d "%~dp0"

REM 환경변수 설정 (이미 설정되어 있지 않으면)
if "%SHOTGUN_API_KEY%"=="" set SHOTGUN_API_KEY=YOUR_API_KEY_HERE
if "%PROJECT_ROOT%"=="" set PROJECT_ROOT=C:\path\to\project
if "%USER%"=="" set USER=%USERNAME%

REM Shotgun 스크립트 이름 (필요시 변경)
if "%SHOTGUN_SCRIPT_NAME%"=="" set SHOTGUN_SCRIPT_NAME=westworld_util

REM API 키 확인
if "%SHOTGUN_API_KEY%"=="YOUR_API_KEY_HERE" (
    echo 경고: SHOTGUN_API_KEY 환경변수가 설정되지 않았습니다.
    echo       이 스크립트를 수정하거나 환경변수를 설정하세요:
    echo.
    echo       set SHOTGUN_API_KEY=your-actual-api-key
    echo       run.bat
    echo.
)

REM 환경 정보 출력
echo ============================================================
echo Westworld IO-Manager
echo ============================================================
echo User: %USER%
echo Project Root: %PROJECT_ROOT%
python --version
echo ============================================================
echo.

REM 애플리케이션 실행 (Rez 비활성화)
python app.py --no-rez %*
