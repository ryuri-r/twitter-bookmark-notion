# -*- coding: utf-8 -*-
"""
run_menu.py
메인 실행 메뉴
"""
import os, sys, subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"

def run(script):
    subprocess.run([sys.executable, BASE_DIR / script], cwd=BASE_DIR)

def main():
    # .env 확인
    if not ENV_FILE.exists():
        print()
        print("[!] 설정 파일이 없습니다. setup.bat을 먼저 실행해주세요.")
        print()
        return

    while True:
        print()
        print("=" * 50)
        print("  트위터 북마크 파이프라인")
        print("=" * 50)
        print()
        print("  1. 북마크 수집   (트위터에서 새 북마크 가져오기)")
        print("  2. 분류          (카테고리별 자동 분류)")
        print("  3. Notion 업로드 (Notion DB에 저장)")
        print("  4. 전체 실행     (1 → 2 → 3 한 번에)")
        print("  5. AI 재분류     (기타 항목 Gemini로 재분류)")
        print("  0. 종료")
        print()

        choice = input("  번호를 입력하세요: ").strip()
        print()

        if choice == "1":
            run("bookmark_sync.py")
        elif choice == "2":
            run("classify_bookmarks.py")
        elif choice == "3":
            db_id_file = BASE_DIR / "notion_db_id.txt"
            if db_id_file.exists():
                run_with_arg("setup_and_upload.py", "--upload")
            else:
                run("setup_and_upload.py")
        elif choice == "4":
            print("[1/3] 북마크 수집 중...")
            run("bookmark_sync.py")
            print("[2/3] 분류 중...")
            run("classify_bookmarks.py")
            print("[3/3] Notion 업로드 중...")
            db_id_file = BASE_DIR / "notion_db_id.txt"
            if db_id_file.exists():
                run_with_arg("setup_and_upload.py", "--upload")
            else:
                run("setup_and_upload.py")
            print()
            print("전체 실행 완료!")
        elif choice == "5":
            run("reclassify_with_gemini.py")
        elif choice == "0":
            print("종료합니다.")
            break
        else:
            print("잘못된 입력입니다.")

def run_with_arg(script, arg):
    subprocess.run([sys.executable, BASE_DIR / script, arg], cwd=BASE_DIR)

if __name__ == "__main__":
    main()
