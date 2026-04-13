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

def validate(value, label, checks):
    """
    checks: list of (조건함수, 경고메시지)
    경고만 띄우고 재입력 기회 줌. 그래도 계속 틀리면 그냥 진행.
    """
    for check_fn, warn_msg in checks:
        if not check_fn(value):
            print(f"  [경고] {warn_msg}")
            print(f"  입력값: {value[:30]}{'...' if len(value) > 30 else ''}")
            retry = ask(f"  다시 입력하려면 새 값을, 그대로 쓰려면 Enter: ")
            if retry:
                value = retry
            break
    return value

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
    ct0        = validate(ct0, "ct0", [
        (lambda v: len(v) >= 20,         "ct0가 너무 짧습니다. 제대로 복사됐는지 확인하세요."),
        (lambda v: " " not in v,         "공백이 포함되어 있습니다. 값만 복사했는지 확인하세요."),
    ])

    auth_token = ask("  auth_token 값: ")
    auth_token = validate(auth_token, "auth_token", [
        (lambda v: len(v) >= 20,         "auth_token이 너무 짧습니다. 제대로 복사됐는지 확인하세요."),
        (lambda v: " " not in v,         "공백이 포함되어 있습니다. 값만 복사했는지 확인하세요."),
    ])
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
    notion_token = validate(notion_token, "Notion 토큰", [
        (lambda v: v.startswith("ntn_") or v.startswith("secret_"),
         "Notion 토큰은 'ntn_' 또는 'secret_'으로 시작해야 합니다. 토큰을 다시 확인하세요."),
    ])
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
    # 하이픈 제거 후 32자리 확인
    page_id_clean = page_id.replace("-", "")
    page_id = validate(page_id, "페이지 ID", [
        (lambda v: len(v.replace("-", "")) == 32,
         f"페이지 ID는 32자리여야 합니다 (현재 {len(page_id_clean)}자리). URL 맨 끝 값을 다시 확인하세요."),
    ])
    print()

    # ── 4단계: AI 재분류 키 (선택) ─────────────────────────────────
    print("━" * 52)
    print("[4단계] AI 재분류 키 (선택 — 없어도 됩니다)")
    print("━" * 52)
    print()
    print("'기타'로 분류된 트윗을 AI가 다시 분류할 때 사용합니다.")
    print("OpenAI 또는 Gemini 중 하나만 있으면 됩니다.")
    print("없으면 그냥 Enter — AI 재분류 기능만 빠지고 나머지는 정상 동작합니다.")
    print()

    openai_key = ask("  OpenAI API 키 (없으면 Enter): ")
    if openai_key:
        openai_key = validate(openai_key, "OpenAI API 키", [
            (lambda v: v.startswith("sk-"),
             "OpenAI API 키는 'sk-'로 시작해야 합니다. 키를 다시 확인하세요."),
        ])

    gemini_key = ""
    if not openai_key:
        gemini_key = ask("  Gemini API 키 (없으면 Enter): ")
        if gemini_key:
            gemini_key = validate(gemini_key, "Gemini API 키", [
                (lambda v: v.startswith("AIza"),
                 "Gemini API 키는 'AIza'로 시작해야 합니다. 키를 다시 확인하세요."),
            ])
    print()

    # ── .env 저장 ───────────────────────────────────────────────────
    lines = [
        f"TWITTER_CT0={ct0}",
        f"TWITTER_AUTH_TOKEN={auth_token}",
        f"NOTION_TOKEN={notion_token}",
        f"NOTION_PARENT_PAGE_ID={page_id}",
        f"OPENAI_API_KEY={openai_key}",
        f"GEMINI_API_KEY={gemini_key}",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")

    # 페이지 ID가 바뀌었으면 기존 DB 기록 삭제 (새 DB 생성하도록)
    db_id_file = BASE_DIR / "notion_db_id.txt"
    if db_id_file.exists():
        db_id_file.unlink()
        print("  기존 Notion DB 기록을 초기화했습니다. 새 DB가 생성됩니다.")

    print("━" * 52)
    print("[완료] 설정 파일(.env)이 생성되었습니다!")
    print("━" * 52)
    print()
    print("이제 run.bat 을 더블클릭해서 실행하세요.")
    print()

if __name__ == "__main__":
    main()
