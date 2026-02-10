#!/bin/bash
#
# Git Commit and Push Helper Script
#
# 사용법:
#   ./git-commit.sh "커밋 메시지"
#   ./git-commit.sh "feat: Add new feature" "상세 설명..."

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Git Commit and Push Helper${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 1. 변경사항 확인
echo -e "${YELLOW}[1/6] Checking git status...${NC}"
if ! git diff-index --quiet HEAD --; then
    echo -e "${GREEN}✓ Changes detected${NC}"
    git status --short
    echo ""
    git diff --stat
    echo ""
else
    echo -e "${RED}✗ No changes to commit${NC}"
    exit 0
fi

# 2. 사용자 확인
echo ""
echo -e "${YELLOW}[2/6] Review changes above${NC}"
read -p "Do you want to continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted${NC}"
    exit 1
fi

# 3. Git Add
echo ""
echo -e "${YELLOW}[3/6] Adding files to staging area...${NC}"
git add .
echo -e "${GREEN}✓ All changes staged${NC}"

# 4. 커밋 메시지 작성
echo ""
echo -e "${YELLOW}[4/6] Creating commit message...${NC}"

# 커밋 메시지가 인자로 전달되었는지 확인
if [ -z "$1" ]; then
    echo -e "${BLUE}Please enter commit message:${NC}"
    echo "Format: <type>: <description>"
    echo "Types: feat, fix, refactor, docs, test, chore, style"
    echo ""
    read -p "Commit message: " COMMIT_MSG
else
    COMMIT_MSG="$1"
fi

# 상세 설명 추가 (선택)
DETAIL=""
if [ ! -z "$2" ]; then
    DETAIL="$2"
else
    echo ""
    read -p "Add detailed description? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Enter detailed description (empty line to finish):"
        while IFS= read -r line; do
            [ -z "$line" ] && break
            DETAIL="${DETAIL}- ${line}\n"
        done
    fi
fi

# 커밋 메시지 구성
FULL_MSG="${COMMIT_MSG}"
if [ ! -z "$DETAIL" ]; then
    FULL_MSG="${FULL_MSG}\n\n${DETAIL}"
fi
FULL_MSG="${FULL_MSG}\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 5. Commit
echo ""
echo -e "${YELLOW}[5/6] Creating commit...${NC}"
echo -e "${FULL_MSG}" | git commit -F -
echo -e "${GREEN}✓ Commit created${NC}"

# 6. Push
echo ""
echo -e "${YELLOW}[6/6] Pushing to remote...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
echo "Pushing to origin/${CURRENT_BRANCH}"

read -p "Push to remote? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin "$CURRENT_BRANCH"
    echo -e "${GREEN}✓ Pushed to origin/${CURRENT_BRANCH}${NC}"
else
    echo -e "${YELLOW}⚠ Commit created but not pushed${NC}"
    echo "To push later, run: git push origin ${CURRENT_BRANCH}"
fi

# 완료
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✓ Done!${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
git log -1 --pretty=format:"%h - %s (%an, %ar)" | cat
echo ""
