# -*- coding: utf-8 -*-
"""
run_menu.py
메인 실행 메뉴 (한국어 / English / 日本語)
"""
import os, sys, subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"

# ── 언어별 텍스트 ──────────────────────────────────────────────────────
STRINGS = {
    "ko": {
        "no_env":  "[!] 설정 파일이 없습니다. setup.bat을 먼저 실행해주세요.",
        "title":   "트위터 북마크 파이프라인",
        "menu": [
            "1. 북마크 수집   (트위터에서 새 북마크 가져오기)",
            "2. 분류          (카테고리별 자동 분류)",
            "3. Notion 업로드 (Notion DB에 저장)",
            "4. 전체 실행     (1 → 2 → 3 한 번에)",
            "5. AI 재분류     (기타 항목 OpenAI/Gemini로 재분류)",
            "6. 전체 재분류   (분류 결과 초기화 후 처음부터 다시)",
            "0. 종료",
        ],
        "input":          "  번호를 입력하세요: ",
        "step1":          "[1/3] 북마크 수집 중...",
        "step2":          "[2/3] 분류 중...",
        "step3":          "[3/3] Notion 업로드 중...",
        "done":           "전체 실행 완료!",
        "reset_confirm":  "분류 결과를 초기화하고 처음부터 다시 분류합니다.\n  계속할까요? (y/n): ",
        "reset_cancel":   "취소했습니다.",
        "quit":           "종료합니다.",
        "invalid":        "잘못된 입력입니다.",
    },
    "en": {
        "no_env":  "[!] Settings file not found. Please run setup.bat first.",
        "title":   "Twitter Bookmark Pipeline",
        "menu": [
            "1. Sync bookmarks   (fetch new bookmarks from Twitter)",
            "2. Classify         (auto-categorize bookmarks)",
            "3. Notion upload    (save to Notion DB)",
            "4. Run all          (1 → 2 → 3 at once)",
            "5. AI reclassify    (reclassify 'Other' with OpenAI/Gemini)",
            "6. Full reclassify  (reset classifications and start over)",
            "0. Quit",
        ],
        "input":          "  Enter number: ",
        "step1":          "[1/3] Syncing bookmarks...",
        "step2":          "[2/3] Classifying...",
        "step3":          "[3/3] Uploading to Notion...",
        "done":           "All done!",
        "reset_confirm":  "This will reset all classifications and start over.\n  Continue? (y/n): ",
        "reset_cancel":   "Cancelled.",
        "quit":           "Goodbye.",
        "invalid":        "Invalid input.",
    },
    "ja": {
        "no_env":  "[!] 設定ファイルが見つかりません。先にsetup.batを実行してください。",
        "title":   "Twitter ブックマーク パイプライン",
        "menu": [
            "1. ブックマーク収集    (Twitterから新しいブックマークを取得)",
            "2. 分類               (カテゴリ別に自動分類)",
            "3. Notion アップロード (Notion DBに保存)",
            "4. 一括実行           (1 → 2 → 3 をまとめて実行)",
            "5. AI 再分類          (「その他」をOpenAI/Geminiで再分類)",
            "6. 全体再分類         (分類結果をリセットして最初からやり直し)",
            "0. 終了",
        ],
        "input":          "  番号を入力してください: ",
        "step1":          "[1/3] ブックマーク収集中...",
        "step2":          "[2/3] 分類中...",
        "step3":          "[3/3] Notion アップロード中...",
        "done":           "すべての処理が完了しました！",
        "reset_confirm":  "分類結果をリセットして最初からやり直します。\n  続けますか？ (y/n): ",
        "reset_cancel":   "キャンセルしました。",
        "quit":           "終了します。",
        "invalid":        "無効な入力です。",
    },
}

def select_language() -> str:
    print()
    print("  언어를 선택하세요 / Select language / 言語を選択してください")
    print()
    print("  1. 한국어")
    print("  2. English")
    print("  3. 日本語")
    print()
    choice = input("  > ").strip()
    if choice == "2":
        return "en"
    elif choice == "3":
        return "ja"
    else:
        return "ko"

def run(script):
    subprocess.run([sys.executable, BASE_DIR / script], cwd=BASE_DIR)

def run_with_arg(script, arg):
    subprocess.run([sys.executable, BASE_DIR / script, arg], cwd=BASE_DIR)

def main():
    lang = select_language()
    s = STRINGS[lang]

    if not ENV_FILE.exists():
        print()
        print(s["no_env"])
        print()
        return

    while True:
        print()
        print("=" * 52)
        print(f"  {s['title']}")
        print("=" * 52)
        print()
        for item in s["menu"]:
            print(f"  {item}")
        print()

        choice = input(s["input"]).strip()
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
            print(s["step1"])
            run("bookmark_sync.py")
            print(s["step2"])
            run("classify_bookmarks.py")
            print(s["step3"])
            db_id_file = BASE_DIR / "notion_db_id.txt"
            if db_id_file.exists():
                run_with_arg("setup_and_upload.py", "--upload")
            else:
                run("setup_and_upload.py")
            print()
            print(s["done"])
        elif choice == "5":
            run("reclassify_ai.py")
        elif choice == "6":
            confirm = input(s["reset_confirm"]).strip().lower()
            if confirm == "y":
                run_with_arg("classify_bookmarks.py", "--reset")
            else:
                print(s["reset_cancel"])
        elif choice == "0":
            print(s["quit"])
            break
        else:
            print(s["invalid"])

if __name__ == "__main__":
    main()
