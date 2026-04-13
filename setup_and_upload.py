"""
setup_and_upload.py
1단계: 트위터 북마크3 페이지에 DB 생성
2단계: classified_bookmarks.jsonl → Notion 업로드

사용법:
    python setup_and_upload.py           (DB 생성 + 전체 업로드)
    python setup_and_upload.py --setup   (DB 생성만)
    python setup_and_upload.py --upload  (이미 DB 있으면 업로드만)
"""

import json, os, sys, time
from pathlib import Path
from urllib import request as ureq
import urllib.error

# ── 설정 ─────────────────────────────────────────────────────────────
# .env 파일 자동 로드 (python-dotenv 없어도 동작하는 간이 로더)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

NOTION_TOKEN    = os.environ.get("NOTION_TOKEN", "")
PARENT_PAGE_ID  = os.environ.get("NOTION_PARENT_PAGE_ID", "")  # Notion에서 북마크 저장할 페이지 ID

BASE_DIR        = Path(__file__).parent
CLASSIFIED_FILE = BASE_DIR / "classified_bookmarks.jsonl"
DB_ID_FILE      = BASE_DIR / "notion_db_id.txt"        # 생성된 DB ID 저장
UPLOADED_FILE   = BASE_DIR / "uploaded_ids.json"

ONLY_SETUP  = "--setup"  in sys.argv
ONLY_UPLOAD = "--upload" in sys.argv

HEADERS = {
    "Authorization":  f"Bearer {NOTION_TOKEN}",
    "Content-Type":   "application/json",
    "Notion-Version": "2022-06-28",
}

def api(method, path, body=None):
    url = f"https://api.notion.com/v1/{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = ureq.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with ureq.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code}: {err[:300]}")

# ── 1단계: DB 생성 ────────────────────────────────────────────────────
def create_db():
    print("DB 생성 중...")
    body = {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE_ID},
        "title": [{"type": "text", "text": {"content": "북마크 DB"}}],
        "properties": {
            "이름": {"title": {}},
            "Category": {"select": {"options": [
                {"name": "뷰티 & 스킨케어",    "color": "pink"},
                {"name": "피트니스 & 다이어트", "color": "green"},
                {"name": "공부 & 학습",        "color": "blue"},
                {"name": "유머 & 밈",          "color": "yellow"},
                {"name": "패션 & 코디",        "color": "purple"},
                {"name": "창작 & 일러스트",    "color": "orange"},
                {"name": "요리 & 레시피",      "color": "red"},
                {"name": "생활 꿀팁 & 정보",   "color": "brown"},
                {"name": "테크 & 도구",        "color": "gray"},
                {"name": "동기부여 & 명언",    "color": "default"},
                {"name": "덕질 & 팬덤",        "color": "blue"},
                {"name": "기타",              "color": "default"},
            ]}},
            "AuthorID":   {"rich_text": {}},
            "AuthorName": {"rich_text": {}},
            "Lang": {"select": {"options": [
                {"name": "ko",  "color": "blue"},
                {"name": "ja",  "color": "red"},
                {"name": "en",  "color": "gray"},
                {"name": "und", "color": "default"},
                {"name": "zxx", "color": "default"},
            ]}},
            "Media":   {"url": {}},
            "Links":   {"url": {}},
            "URL":     {"url": {}},
            "Text":    {"rich_text": {}},
            "Tags":    {"multi_select": {}},
            "TweetAt": {"date": {}},
            "SavedAt": {"date": {}},
        },
    }
    result = api("POST", "databases", body)
    db_id = result["id"].replace("-", "")
    DB_ID_FILE.write_text(db_id)
    print(f"DB 생성 완료: {db_id}")
    print(f"DB URL: https://www.notion.so/{db_id}")
    return db_id

# ── 2단계: 업로드 ─────────────────────────────────────────────────────
def load_uploaded():
    if UPLOADED_FILE.exists():
        return set(json.loads(UPLOADED_FILE.read_text()))
    return set()

def save_uploaded(uploaded: set):
    UPLOADED_FILE.write_text(json.dumps(list(uploaded)))

def make_page(bm: dict, db_id: str) -> dict:
    title = (bm.get("text") or "")[:80].strip().replace("\n", " ") or f"Tweet {bm.get('id','?')}"

    props = {
        "이름":       {"title": [{"text": {"content": title}}]},
        "URL":        {"url": bm.get("url") or None},
        "AuthorID":   {"rich_text": [{"text": {"content": bm.get("authorHandle", "")}}]},
        "AuthorName": {"rich_text": [{"text": {"content": bm.get("authorName", "")}}]},
        "Category":   {"select": {"name": bm.get("categoryLabel", "기타")}},
        "Text":       {"rich_text": [{"text": {"content": (bm.get("text") or "")[:2000]}}]},
    }

    lang = bm.get("language")
    if lang:
        props["Lang"] = {"select": {"name": lang}}

    media = bm.get("media", [])
    if media and media[0]:
        props["Media"] = {"url": media[0]}

    links = bm.get("links", [])
    if links and links[0]:
        props["Links"] = {"url": links[0]}

    posted = bm.get("postedAt")
    if posted:
        try:
            from datetime import datetime
            dt = datetime.strptime(posted, "%a %b %d %H:%M:%S +0000 %Y")
            props["TweetAt"] = {"date": {"start": dt.strftime("%Y-%m-%d")}}
        except Exception:
            pass

    synced = bm.get("syncedAt")
    if synced:
        props["SavedAt"] = {"date": {"start": synced[:10]}}

    tags = bm.get("tags", [])
    if tags:
        props["Tags"] = {"multi_select": [{"name": t[:100]} for t in tags[:10]]}

    page = {
        "parent": {"database_id": db_id},
        "properties": props,
    }
    if media and media[0]:
        page["cover"] = {"type": "external", "external": {"url": media[0]}}

    return page

def upload(db_id: str):
    bookmarks = []
    with open(CLASSIFIED_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                bookmarks.append(json.loads(line.strip()))
            except Exception:
                pass

    uploaded = load_uploaded()
    to_upload = [b for b in bookmarks if b.get("id") not in uploaded]
    print(f"업로드 대상: {len(to_upload)}개 (전체 {len(bookmarks)}개 중)")

    if not to_upload:
        print("업로드할 항목 없음.")
        return

    print(f"예상 시간: 약 {len(to_upload) * 0.35 / 60:.0f}분\n")

    success, fail = 0, 0
    start = time.time()

    for i, bm in enumerate(to_upload, 1):
        try:
            page = make_page(bm, db_id)
            api("POST", "pages", page)
            success += 1
            uploaded.add(bm["id"])
            if i % 50 == 0:
                save_uploaded(uploaded)
                elapsed = time.time() - start
                eta = (elapsed / i) * (len(to_upload) - i)
                print(f"  [{i}/{len(to_upload)}] 성공 {success} / 실패 {fail}  (남은 ~{eta/60:.1f}분)", end="\r")
        except Exception as e:
            fail += 1
            if fail <= 3:
                print(f"\n  [오류] {bm.get('id','?')}: {e}")
            if fail >= 10 and success == 0:
                print("\n연속 오류 — 토큰 또는 DB 연결 확인 필요")
                break
        time.sleep(0.35)

    save_uploaded(uploaded)
    elapsed = time.time() - start
    print(f"\n\n완료: 성공 {success}개 / 실패 {fail}개  ({elapsed/60:.1f}분)")

# ── 메인 ─────────────────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  트위터 북마크 → Notion 셋업 & 업로드")
    print("=" * 50 + "\n")

    if not NOTION_TOKEN:
        print("오류: NOTION_TOKEN이 설정되지 않았습니다.")
        print("setup.bat을 실행해서 토큰을 먼저 입력해주세요.")
        sys.exit(1)
    if not PARENT_PAGE_ID:
        print("오류: NOTION_PARENT_PAGE_ID가 설정되지 않았습니다.")
        print("setup.bat을 실행해서 Notion 페이지 ID를 먼저 입력해주세요.")
        sys.exit(1)

    if ONLY_UPLOAD:
        # DB ID 기존 파일에서 읽기
        if not DB_ID_FILE.exists():
            print("오류: notion_db_id.txt 없음. --setup 먼저 실행하세요.")
            sys.exit(1)
        db_id = DB_ID_FILE.read_text().strip()
        print(f"기존 DB 사용: {db_id}")
        upload(db_id)
        return

    if ONLY_SETUP:
        create_db()
        return

    # 기본: DB 생성 + 업로드
    db_id = create_db()
    print()
    upload(db_id)

if __name__ == "__main__":
    main()
