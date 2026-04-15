# -*- coding: utf-8 -*-
"""
setup_wizard.py
최초 설정 마법사 (한국어 / English / 日本語)
"""
import os, sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"

# ── 언어별 텍스트 ──────────────────────────────────────────────────────
STRINGS = {
    "ko": {
        "title":            "트위터 북마크 파이프라인  최초 설정",
        "py_error":         "[오류] Python 3.8 이상이 필요합니다.",
        "py_ok":            "[OK] Python {ver} 확인",
        "env_exists":       "이미 설정 파일(.env)이 있습니다. 덮어쓸까요? (y/n): ",
        "env_keep":         "설정을 유지합니다.",
        # Step 1
        "step1_title":      "[1단계] 트위터 토큰 입력",
        "step1_guide": (
            "크롬/엣지에서 x.com 로그인 후:\n"
            "  F12 → Application → Cookies → https://x.com\n"
            "  ct0 와 auth_token 값을 복사해서 붙여넣으세요."
        ),
        "ask_ct0":          "  ct0 값: ",
        "ask_auth":         "  auth_token 값: ",
        "warn_short":       "{key}가 너무 짧습니다. 제대로 복사됐는지 확인하세요.",
        "warn_space":       "공백이 포함되어 있습니다. 값만 복사했는지 확인하세요.",
        # Step 2
        "step2_title":      "[2단계] Notion 토큰 입력",
        "step2_guide": (
            "https://www.notion.so/my-integrations 에서:\n"
            "  '+ 새 API 통합 만들기' → 이름 입력 → 제출\n"
            "  '내부 통합 시크릿' 복사 후 붙여넣으세요."
        ),
        "ask_notion":       "  Notion 토큰: ",
        "warn_notion":      "Notion 토큰은 'ntn_' 또는 'secret_'으로 시작해야 합니다. 토큰을 다시 확인하세요.",
        # Step 3
        "step3_title":      "[3단계] Notion 페이지 ID 입력",
        "step3_guide": (
            "북마크 DB를 만들 Notion 페이지 URL 맨 끝 32자리를 복사하세요.\n"
            "  예: notion.so/페이지이름-[abc123def456abc123def456abc123de]\n"
            "\n"
            "그 페이지에서 '...' → '연결' → 방금 만든 통합 연결도 잊지 마세요!"
        ),
        "ask_page":         "  페이지 ID: ",
        "warn_page":        "페이지 ID는 32자리여야 합니다 (현재 {n}자리). URL 맨 끝 값을 다시 확인하세요.",
        # Step 4
        "step4_title":      "[4단계] AI 재분류 키 (선택 — 없어도 됩니다)",
        "step4_guide": (
            "'기타'로 분류된 트윗을 AI가 다시 분류할 때 사용합니다.\n"
            "OpenAI 또는 Gemini 중 하나만 있으면 됩니다.\n"
            "없으면 그냥 Enter — AI 재분류 기능만 빠지고 나머지는 정상 동작합니다."
        ),
        "ask_openai":       "  OpenAI API 키 (없으면 Enter): ",
        "warn_openai":      "OpenAI API 키는 'sk-'로 시작해야 합니다. 키를 다시 확인하세요.",
        "ask_gemini":       "  Gemini API 키 (없으면 Enter): ",
        "warn_gemini":      "Gemini API 키는 'AIza'로 시작해야 합니다. 키를 다시 확인하세요.",
        # 완료
        "done_title":       "[완료] 설정 파일(.env)이 생성되었습니다!",
        "done_guide":       "이제 run.bat 을 더블클릭해서 실행하세요.",
        "db_reset":         "  기존 Notion DB 기록 초기화 → 새 DB가 생성됩니다.",
        "upload_confirm":   "  기존 업로드 기록도 초기화할까요? (새 DB에 전부 다시 올리려면 y): ",
        "upload_reset":     "  업로드 기록 초기화 완료.",
        "retry":            "  다시 입력하려면 새 값을, 그대로 쓰려면 Enter: ",
    },
    "en": {
        "title":            "Twitter Bookmark Pipeline  Initial Setup",
        "py_error":         "[Error] Python 3.8 or higher is required.",
        "py_ok":            "[OK] Python {ver} detected",
        "env_exists":       "Settings file (.env) already exists. Overwrite? (y/n): ",
        "env_keep":         "Settings unchanged.",
        # Step 1
        "step1_title":      "[Step 1] Enter Twitter tokens",
        "step1_guide": (
            "Log in to x.com on Chrome or Edge, then:\n"
            "  F12 → Application → Cookies → https://x.com\n"
            "  Copy the ct0 and auth_token values and paste them below."
        ),
        "ask_ct0":          "  ct0 value: ",
        "ask_auth":         "  auth_token value: ",
        "warn_short":       "{key} is too short. Please check you copied it correctly.",
        "warn_space":       "Contains spaces. Make sure you copied only the value.",
        # Step 2
        "step2_title":      "[Step 2] Enter Notion token",
        "step2_guide": (
            "Go to https://www.notion.so/my-integrations\n"
            "  Click '+ New integration' → Enter a name → Submit\n"
            "  Copy 'Internal Integration Secret' and paste it below."
        ),
        "ask_notion":       "  Notion token: ",
        "warn_notion":      "Notion token must start with 'ntn_' or 'secret_'. Please check.",
        # Step 3
        "step3_title":      "[Step 3] Enter Notion page ID",
        "step3_guide": (
            "Copy the last 32 characters from your Notion page URL.\n"
            "  Example: notion.so/page-name-[abc123def456abc123def456abc123de]\n"
            "\n"
            "Also: click '...' → 'Connect to' → add your integration!"
        ),
        "ask_page":         "  Page ID: ",
        "warn_page":        "Page ID must be 32 characters (currently {n}). Check the end of the URL.",
        # Step 4
        "step4_title":      "[Step 4] AI reclassify key (optional)",
        "step4_guide": (
            "Used to reclassify tweets marked as 'Other' using AI.\n"
            "You only need one of OpenAI or Gemini.\n"
            "Press Enter to skip — all other features will work normally."
        ),
        "ask_openai":       "  OpenAI API key (Enter to skip): ",
        "warn_openai":      "OpenAI API key must start with 'sk-'. Please check.",
        "ask_gemini":       "  Gemini API key (Enter to skip): ",
        "warn_gemini":      "Gemini API key must start with 'AIza'. Please check.",
        # Done
        "done_title":       "[Done] Settings file (.env) created!",
        "done_guide":       "Now double-click run.bat to start.",
        "db_reset":         "  Previous Notion DB record cleared → a new DB will be created.",
        "upload_confirm":   "  Reset existing upload records too? (re-upload everything to new DB: y): ",
        "upload_reset":     "  Upload records cleared.",
        "retry":            "  Type a new value to re-enter, or press Enter to keep: ",
    },
    "ja": {
        "title":            "Twitter ブックマーク パイプライン  初期設定",
        "py_error":         "[エラー] Python 3.8 以上が必要です。",
        "py_ok":            "[OK] Python {ver} を確認しました",
        "env_exists":       "設定ファイル(.env)がすでに存在します。上書きしますか？ (y/n): ",
        "env_keep":         "設定を維持します。",
        # Step 1
        "step1_title":      "[ステップ1] Twitter トークンを入力",
        "step1_guide": (
            "ChromeまたはEdgeでx.comにログインしてから:\n"
            "  F12 → Application → Cookies → https://x.com\n"
            "  ct0 と auth_token の値をコピーして貼り付けてください。"
        ),
        "ask_ct0":          "  ct0 の値: ",
        "ask_auth":         "  auth_token の値: ",
        "warn_short":       "{key} が短すぎます。正しくコピーされているか確認してください。",
        "warn_space":       "スペースが含まれています。値のみコピーしているか確認してください。",
        # Step 2
        "step2_title":      "[ステップ2] Notion トークンを入力",
        "step2_guide": (
            "https://www.notion.so/my-integrations にアクセスして:\n"
            "  '+ 新しいインテグレーションを作成' → 名前を入力 → 送信\n"
            "  '内部インテグレーションシークレット' をコピーして貼り付けてください。"
        ),
        "ask_notion":       "  Notion トークン: ",
        "warn_notion":      "Notion トークンは 'ntn_' または 'secret_' で始まる必要があります。",
        # Step 3
        "step3_title":      "[ステップ3] Notion ページ ID を入力",
        "step3_guide": (
            "Notion ページの URL の末尾32文字をコピーしてください。\n"
            "  例: notion.so/ページ名-[abc123def456abc123def456abc123de]\n"
            "\n"
            "そのページで '...' → '接続' → 作成したインテグレーションを追加するのもお忘れなく！"
        ),
        "ask_page":         "  ページ ID: ",
        "warn_page":        "ページ ID は32文字である必要があります（現在 {n} 文字）。URLの末尾を再確認してください。",
        # Step 4
        "step4_title":      "[ステップ4] AI 再分類キー（任意）",
        "step4_guide": (
            "「その他」に分類されたツイートをAIが再分類するときに使用します。\n"
            "OpenAI または Gemini のどちらか一方だけで構いません。\n"
            "不要な場合はそのままEnterを押してください。他の機能は正常に動作します。"
        ),
        "ask_openai":       "  OpenAI API キー（スキップする場合はEnter）: ",
        "warn_openai":      "OpenAI API キーは 'sk-' で始まる必要があります。",
        "ask_gemini":       "  Gemini API キー（スキップする場合はEnter）: ",
        "warn_gemini":      "Gemini API キーは 'AIza' で始まる必要があります。",
        # 完了
        "done_title":       "[完了] 設定ファイル(.env)が作成されました！",
        "done_guide":       "run.bat をダブルクリックして実行してください。",
        "db_reset":         "  既存の Notion DB 記録を初期化しました → 新しい DB が作成されます。",
        "upload_confirm":   "  既存のアップロード記録もリセットしますか？（新しいDBに全て再アップロードする場合: y）: ",
        "upload_reset":     "  アップロード記録を初期化しました。",
        "retry":            "  再入力する場合は新しい値を、そのまま使う場合はEnterを押してください: ",
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

def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return ""

def validate(s, value, checks):
    for check_fn, warn_msg in checks:
        if not check_fn(value):
            print(f"  [!] {warn_msg}")
            print(f"  > {value[:30]}{'...' if len(value) > 30 else ''}")
            retry = ask(s["retry"])
            if retry:
                value = retry
            break
    return value

def main():
    lang = select_language()
    s = STRINGS[lang]

    print("=" * 52)
    print(f"  {s['title']}")
    print("=" * 52)
    print()

    # Python 버전 확인
    if sys.version_info < (3, 8):
        print(s["py_error"])
        print(f"  {sys.version}")
        return

    print(s["py_ok"].format(ver=sys.version.split()[0]))
    print()

    # .env 존재 확인
    if ENV_FILE.exists():
        ans = ask(s["env_exists"])
        if ans.lower() != "y":
            print(s["env_keep"])
            return
        print()

    # ── Step 1: 트위터 토큰 ────────────────────────────────────────────
    print("━" * 52)
    print(s["step1_title"])
    print("━" * 52)
    print()
    print(s["step1_guide"])
    print()

    ct0 = ask(s["ask_ct0"])
    ct0 = validate(s, ct0, [
        (lambda v: len(v) >= 20, s["warn_short"].format(key="ct0")),
        (lambda v: " " not in v, s["warn_space"]),
    ])

    auth_token = ask(s["ask_auth"])
    auth_token = validate(s, auth_token, [
        (lambda v: len(v) >= 20, s["warn_short"].format(key="auth_token")),
        (lambda v: " " not in v, s["warn_space"]),
    ])
    print()

    # ── Step 2: Notion 토큰 ───────────────────────────────────────────
    print("━" * 52)
    print(s["step2_title"])
    print("━" * 52)
    print()
    print(s["step2_guide"])
    print()

    notion_token = ask(s["ask_notion"])
    notion_token = validate(s, notion_token, [
        (lambda v: v.startswith("ntn_") or v.startswith("secret_"), s["warn_notion"]),
    ])
    print()

    # ── Step 3: Notion 페이지 ID ──────────────────────────────────────
    print("━" * 52)
    print(s["step3_title"])
    print("━" * 52)
    print()
    print(s["step3_guide"])
    print()

    page_id = ask(s["ask_page"])
    page_id_clean = page_id.replace("-", "")
    page_id = validate(s, page_id, [
        (lambda v: len(v.replace("-", "")) == 32,
         s["warn_page"].format(n=len(page_id_clean))),
    ])
    print()

    # ── Step 4: AI 키 (선택) ──────────────────────────────────────────
    print("━" * 52)
    print(s["step4_title"])
    print("━" * 52)
    print()
    print(s["step4_guide"])
    print()

    openai_key = ask(s["ask_openai"])
    if openai_key:
        openai_key = validate(s, openai_key, [
            (lambda v: v.startswith("sk-"), s["warn_openai"]),
        ])

    gemini_key = ""
    if not openai_key:
        gemini_key = ask(s["ask_gemini"])
        if gemini_key:
            gemini_key = validate(s, gemini_key, [
                (lambda v: v.startswith("AIza"), s["warn_gemini"]),
            ])
    print()

    # ── .env 저장 ──────────────────────────────────────────────────────
    lines = [
        f"TWITTER_CT0={ct0}",
        f"TWITTER_AUTH_TOKEN={auth_token}",
        f"NOTION_TOKEN={notion_token}",
        f"NOTION_PARENT_PAGE_ID={page_id}",
        f"OPENAI_API_KEY={openai_key}",
        f"GEMINI_API_KEY={gemini_key}",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")

    # DB 기록 초기화
    db_id_file = BASE_DIR / "notion_db_id.txt"
    if db_id_file.exists():
        db_id_file.unlink()
        print(s["db_reset"])

    # 업로드 기록 초기화 여부 확인
    uploaded_file = BASE_DIR / "uploaded_ids.json"
    if uploaded_file.exists():
        ans = ask(s["upload_confirm"])
        if ans.lower() == "y":
            uploaded_file.unlink()
            print(s["upload_reset"])

    print("━" * 52)
    print(s["done_title"])
    print("━" * 52)
    print()
    print(s["done_guide"])
    print()

if __name__ == "__main__":
    main()
