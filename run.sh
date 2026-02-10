#!/bin/bash
#
# IO Manager 실행 스크립트
#
# 사용법:
#   ./run.sh
#
# 환경변수:
#   SHOTGUN_API_KEY       Shotgun API 키 (필수)
#   PROJECT_ROOT          프로젝트 루트 경로 (선택)
#   USER                  사용자 이름 (선택, 기본값: 현재 사용자)

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 환경변수 설정
export SHOTGUN_API_KEY="${SHOTGUN_API_KEY:-YOUR_API_KEY_HERE}"
export PROJECT_ROOT="${PROJECT_ROOT:-/path/to/project}"
export USER="${USER:-$(whoami)}"

# Shotgun 스크립트 이름 (필요시 변경)
export SHOTGUN_SCRIPT_NAME="${SHOTGUN_SCRIPT_NAME:-westworld_util}"

# API 키 확인
if [ "$SHOTGUN_API_KEY" = "YOUR_API_KEY_HERE" ]; then
    echo "경고: SHOTGUN_API_KEY 환경변수가 설정되지 않았습니다."
    echo "      이 스크립트를 수정하거나 환경변수를 설정하세요:"
    echo ""
    echo "      export SHOTGUN_API_KEY='your-actual-api-key'"
    echo "      ./run.sh"
    echo ""
fi

# 환경 정보 출력
echo "============================================================"
echo "Westworld IO-Manager"
echo "============================================================"
echo "User: $USER"
echo "Project Root: $PROJECT_ROOT"
echo "Python: $(python --version 2>&1)"
echo "============================================================"
echo ""

# 애플리케이션 실행 (Rez 비활성화)
python app.py --no-rez "$@"
