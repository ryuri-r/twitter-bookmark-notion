@echo off
chcp 65001 > nul
title 트위터 북마크 파이프라인

:MENU
cls
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║       트위터 북마크 파이프라인                ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: .env 존재 확인
if not exist ".env" (
    echo  [!] 설정 파일이 없습니다. setup.bat을 먼저 실행해주세요.
    echo.
    pause
    exit /b 1
)

echo  ┌─────────────────────────────────────────────┐
echo  │  1. 북마크 수집   (트위터에서 새 북마크 가져오기)  │
echo  │  2. 분류          (카테고리별 자동 분류)           │
echo  │  3. Notion 업로드 (Notion DB에 저장)               │
echo  │  4. 전체 실행     (1 → 2 → 3 한 번에)              │
echo  │  5. AI 재분류     (기타 항목 Gemini로 재분류)       │
echo  │  0. 종료                                           │
echo  └─────────────────────────────────────────────┘
echo.
set /p CHOICE="  번호를 입력하세요: "

if "%CHOICE%"=="1" goto SYNC
if "%CHOICE%"=="2" goto CLASSIFY
if "%CHOICE%"=="3" goto UPLOAD
if "%CHOICE%"=="4" goto ALL
if "%CHOICE%"=="5" goto GEMINI
if "%CHOICE%"=="0" goto END
echo  잘못된 입력입니다.
timeout /t 1 > nul
goto MENU

:SYNC
echo.
echo  ─── 북마크 수집 중... ───────────────────────────
python bookmark_sync.py
echo.
echo  완료! 아무 키나 누르면 메뉴로 돌아갑니다.
pause > nul
goto MENU

:CLASSIFY
echo.
echo  ─── 분류 중... ──────────────────────────────────
python classify_bookmarks.py
echo.
echo  완료! 아무 키나 누르면 메뉴로 돌아갑니다.
pause > nul
goto MENU

:UPLOAD
echo.
echo  ─── Notion 업로드 중... ─────────────────────────
echo  (처음 실행 시 Notion DB가 자동 생성됩니다)
python setup_and_upload.py --upload
if errorlevel 1 (
    echo.
    echo  DB가 없습니다. DB를 먼저 생성합니다...
    python setup_and_upload.py
)
echo.
echo  완료! 아무 키나 누르면 메뉴로 돌아갑니다.
pause > nul
goto MENU

:ALL
echo.
echo  ─── 전체 실행 (수집 → 분류 → 업로드) ──────────
echo.
echo  [1/3] 북마크 수집 중...
python bookmark_sync.py
if errorlevel 1 goto ERROR

echo.
echo  [2/3] 분류 중...
python classify_bookmarks.py
if errorlevel 1 goto ERROR

echo.
echo  [3/3] Notion 업로드 중...
python setup_and_upload.py --upload 2>nul
if errorlevel 1 (
    python setup_and_upload.py
)

echo.
echo  ─── 전체 완료! ──────────────────────────────────
echo  아무 키나 누르면 메뉴로 돌아갑니다.
pause > nul
goto MENU

:GEMINI
echo.
echo  ─── Gemini AI 재분류 중... ──────────────────────
python reclassify_with_gemini.py
echo.
echo  완료! 아무 키나 누르면 메뉴로 돌아갑니다.
pause > nul
goto MENU

:ERROR
echo.
echo  [오류] 실행 중 문제가 발생했습니다.
echo  위의 오류 메시지를 확인해주세요.
pause > nul
goto MENU

:END
echo.
echo  종료합니다.
timeout /t 1 > nul
