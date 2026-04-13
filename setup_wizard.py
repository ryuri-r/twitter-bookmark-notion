# -*- coding: utf-8 -*-
"""
setup_wizard.py
최초 설정 마법사 — 토큰 입력받아 .env 생성
"""
import os, sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"

def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return ""

def main():
    print("=" * 52)
    print("  트위터 북마크 파이프라인  최초 설정")
    print("=" * 52)
    print()

    # Python 버전 확인
    if sys.version_info < (3, 8):
        print("[오류] Python 3.8 이상이 필요합니다.")
        print(f"  현재 버전: {sys.version}")
        return

    print(f"[OK] Python {sys.version.split()[0]} 확인")
    print()

    # 이미 .env 있으면 확인
    if ENV_FILE.exists():
        ans = ask("이미 설정 파일(.env)이 있습니다. 덮어쓸까요? (y/n): ")
        if ans.lower() != "y":
            print("설정을 유지합니다.")
            return
        print()

    # ── 1단계: 트위터 토큰 ──────────────────────────────────────────
    print("━" * 52)
    print("[1단계] 트위터 토큰 입력")
    print("━" * 52)
    print()
    print("크롬/엣지에서 x.com 로그인 후:")
    print("  F12 → Application → Cookies → https://x.com")
    print("  ct0 와 auth_token 값을 복사해서 붙여넣으세요.")
    print()
    ct0        = ask("  ct0 값: ")
    auth_token = ask("  auth_token 값: ")
    print()

    # ── 2단계: Notion 토큰 ──────────────────────────────────────────
    print("━" * 52)
    print("[2단계] Notion 토큰 입력")
    print("━" * 52)
    print()
    print("https://www.notion.so/my-integrations 에서:")
    print("  '+ 새 API 통합 만들기' → 이름 입력 → 제출")
    print("  '내부 통합 시크릿' 복사 후 붙여넣으세요.")
    print()
    notion_token = ask("  Notion 토큰: ")
    print()

    # ── 3단계: Notion 페이지 ID ─────────────────────────────────────
    print("━" * 52)
    print("[3단계] Notion 페이지 ID 입력")
    print("━" * 52)
    print()
    print("북마크 DB를 만들 Notion 페이지 URL 맨 끝 32자리를 복사하세요.")
    print("  예: notion.so/페이지이름-[abc123def456abc123def456abc123de]")
    print()
    print("그 페이지에서 '...' → '연결' → 방금 만든 통합 연결도 잊지 마세요!")
    print()
    page_id = ask("  페이지 ID: ")
    print()

    # ── 4단계: Gemini (선택) ────────────────────────────────────────
    print("━" * 52)
    print("[4단계] Gemini API 키 (선택 — 없어도 됩니다)")
    print("━" * 52)
    print()
    print("'기타'로 분류된 트윗을 AI가 재분류할 때만 필요합니다.")
    print("https://aistudio.google.com/app/apikey 에서 무료 발급 가능.")
    print("없으면 그냥 Enter를 누르세요.")
    print()
    gemini_key = ask("  Gemini API 키 (없으면 Enter): ")
    print()

    # ── .env 저장 ───────────────────────────────────────────────────
    lines = [
        f"TWITTER_CT0={ct0}",
        f"TWITTER_AUTH_TOKEN={auth_token}",
        f"NOTION_TOKEN={notion_token}",
        f"NOTION_PARENT_PAGE_ID={page_id}",
        f"GEMINI_API_KEY={gemini_key}",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")

    print("━" * 52)
    print("[완료] 설정 파일(.env)이 생성되었습니다!")
    print("━" * 52)
    print()
    print("이제 run.bat 을 더블클릭해서 실행하세요.")
    print()

if __name__ == "__main__":
    main()
