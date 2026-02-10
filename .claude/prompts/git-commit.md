# Git Commit and Push

변경된 파일들을 git에 추가하고, 커밋하고, 푸시하는 프롬프트입니다.

## 사용법

이 프롬프트를 사용하면:
1. 변경된 파일 목록 확인
2. 모든 변경사항을 staging area에 추가
3. 의미있는 커밋 메시지 자동 생성
4. 원격 저장소에 푸시

## 지침

다음 단계를 순차적으로 실행하세요:

### 1. 변경사항 확인
```bash
git status
git diff --stat
```

### 2. 변경된 파일 분석
- 어떤 파일들이 수정되었는지 확인
- 변경 내용의 카테고리 파악 (버그 수정, 새 기능, 리팩토링, 문서 등)

### 3. Git Add
```bash
# 특정 파일만 추가
git add <file1> <file2> ...

# 또는 모든 변경사항 추가
git add .
```

### 4. 커밋 메시지 생성
변경 내용을 바탕으로 다음 형식의 커밋 메시지를 작성:

```
<타입>: <간단한 설명>

<상세 설명>
- 변경사항 1
- 변경사항 2
- 변경사항 3

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**타입**:
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `refactor`: 코드 리팩토링
- `docs`: 문서 변경
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경
- `style`: 코드 포맷팅

### 5. 커밋 실행
```bash
git commit -m "$(cat <<'EOF'
커밋 메시지 여기에 작성

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### 6. 푸시
```bash
# 현재 브랜치를 원격에 푸시
git push

# 또는 특정 브랜치 지정
git push origin main
```

### 7. 확인
```bash
git log -1
```

## 예시

### 예시 1: 버그 수정
```bash
git add python/app/api/excel.py
git commit -m "$(cat <<'EOF'
fix: UnboundLocalError in _get_thumbnail function

- Remove duplicate 'import os' inside function
- os module already imported at file level
- Fixes local variable shadowing issue

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
git push
```

### 예시 2: 새 기능 추가
```bash
git add run.sh run.bat README.md
git commit -m "$(cat <<'EOF'
feat: Add execution scripts for easy startup

- Add run.sh for macOS/Linux
- Add run.bat for Windows
- Scripts set environment variables automatically
- Update README.md with usage instructions

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
git push
```

### 예시 3: 여러 타입의 변경
```bash
git add app.py python/app/api/excel.py requirements-vfx.txt INSTALL.md
git commit -m "$(cat <<'EOF'
feat: Support local oiiotool in --no-rez mode

- Add USE_REZ environment variable in app.py
- Modify excel.py to use local oiiotool when --no-rez
- Add OpenImageIO to requirements-vfx.txt
- Update INSTALL.md with oiiotool installation guide

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
git push
```

## 주의사항

1. **커밋 전 확인**:
   - `git diff` 로 변경사항 검토
   - 불필요한 파일 제외 (`.pyc`, `__pycache__`, `.DS_Store` 등)
   - `.gitignore`가 올바르게 설정되었는지 확인

2. **커밋 메시지**:
   - 명확하고 구체적으로 작성
   - 왜 변경했는지(why) 설명 포함
   - 50자 이내의 제목, 72자 이내의 본문 줄

3. **푸시 전**:
   - 테스트 실행 확인
   - 문법 오류 없는지 확인
   - 민감한 정보(API 키, 비밀번호) 포함 여부 확인

4. **브랜치 전략**:
   - 큰 변경사항은 feature 브랜치 사용
   - main 브랜치에 직접 푸시하기 전에 리뷰 고려
