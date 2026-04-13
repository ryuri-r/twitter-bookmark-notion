@echo off
chcp 65001 > nul
title 트위터 북마크 파이프라인 - 최초 설정

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║     트위터 북마크 파이프라인  최초 설정       ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ─── Python 설치 확인 ──────────────────────────────────────────────
python --version > nul 2>&1
if errorlevel 1 (
    echo  [오류] Python이 설치되어 있지 않습니다.
    echo.
    echo  아래 주소에서 Python을 설치해주세요:
    echo  https://www.python.org/downloads/
    echo.
    echo  설치 시 주의사항:
    echo  "Add Python to PATH" 체크박스를 반드시 체크하세요!
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)
echo  [OK] Python 설치 확인 완료
echo.

:: ─── 이미 .env 있으면 확인 ──────────────────────────────────────────
if exist ".env" (
    echo  이미 설정 파일(.env)이 존재합니다.
    set /p OVERWRITE="덮어쓸까요? (y/n): "
    if /i not "%OVERWRITE%"=="y" (
        echo  설정을 유지합니다. 종료합니다.
        pause
        exit /b 0
    )
    echo.
)

echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [1단계] 트위터 토큰 입력
echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  크롬/엣지에서 x.com(트위터)에 로그인한 뒤:
echo    1. F12 키를 누르세요
echo    2. 상단 탭에서 "Application" 클릭
echo    3. 왼쪽 "Cookies" 아래 "https://x.com" 클릭
echo    4. 아래 두 값을 찾아서 Value 열을 복사하세요
echo.
set /p CT0="  ct0 값을 붙여넣으세요: "
set /p AUTH_TOKEN="  auth_token 값을 붙여넣으세요: "
echo.

echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [2단계] Notion 토큰 입력
echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  https://www.notion.so/my-integrations 에서:
echo    1. "+ 새 API 통합 만들기" 클릭
echo    2. 이름 입력 후 제출
echo    3. "내부 통합 시크릿" 복사
echo.
set /p NOTION_TOKEN="  Notion 토큰을 붙여넣으세요: "
echo.

echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [3단계] Notion 페이지 ID 입력
echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  북마크를 저장할 Notion 페이지 URL에서 마지막 32자리를 복사하세요.
echo  예시: https://notion.so/페이지이름-[이부분이-페이지ID입니다]
echo.
echo  ※ 그 페이지에서 "..." 메뉴 → "연결" → 방금 만든 통합을 연결하는 것 잊지 마세요!
echo.
set /p PAGE_ID="  페이지 ID를 붙여넣으세요: "
echo.

echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [4단계] Gemini API 키 입력 (선택 - 없어도 됩니다)
echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  "기타"로 분류된 트윗을 AI가 다시 분류할 때만 필요합니다.
echo  https://aistudio.google.com/app/apikey 에서 무료로 발급받을 수 있습니다.
echo  건너뛰려면 그냥 Enter를 누르세요.
echo.
set /p GEMINI_KEY="  Gemini API 키 (없으면 Enter): "
echo.

:: ─── .env 파일 생성 ──────────────────────────────────────────────────
(
echo TWITTER_CT0=%CT0%
echo TWITTER_AUTH_TOKEN=%AUTH_TOKEN%
echo NOTION_TOKEN=%NOTION_TOKEN%
echo NOTION_PARENT_PAGE_ID=%PAGE_ID%
echo GEMINI_API_KEY=%GEMINI_KEY%
) > .env

echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo  [완료] 설정 파일(.env)이 생성되었습니다!
echo  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  이제 run.bat을 실행하면 됩니다.
echo.
pause
