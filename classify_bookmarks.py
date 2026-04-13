"""
classify_bookmarks.py
bookmarks.jsonl → 카테고리/태그 분류 → classified_bookmarks.jsonl

사용법:
    python classify_bookmarks.py
    python classify_bookmarks.py --reset   (이미 분류된 것도 재분류)

설정:
    - categories.json 을 편집해서 분류 기준 조정
    - NOTION_PUSH = True 로 바꾸면 Notion에도 자동 업로드
"""

import json, os, sys, re
from pathlib import Path

# ── 경로 설정 ─────────────────────────────────────────────────────────
BASE_DIR          = Path(__file__).parent
BOOKMARKS_FILE    = BASE_DIR / "bookmarks.jsonl"       # bookmark_sync.py가 같은 폴더에 생성
CATEGORIES_FILE   = BASE_DIR / "categories.json"
OUTPUT_FILE       = BASE_DIR / "classified_bookmarks.jsonl"

# ── .env 자동 로드 ────────────────────────────────────────────────────
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ── 옵션 ─────────────────────────────────────────────────────────────
NOTION_PUSH       = False   # True로 바꾸면 분류 후 Notion 자동 업로드
NOTION_TOKEN      = os.environ.get("NOTION_TOKEN", "")
NOTION_DB_ID      = os.environ.get("NOTION_DB_ID", "")  # setup_and_upload.py 실행 후 자동 생성
RESET_CLASSIFIED  = "--reset" in sys.argv

# ── 카테고리 로드 ─────────────────────────────────────────────────────
def load_categories():
    with open(CATEGORIES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["categories"]

def classify(text: str, categories: list) -> tuple[str, str]:
    """
    텍스트를 분석해서 (category_id, category_label) 반환.
    keywords 순서대로 매칭 → 먼저 나온 카테고리 우선.
    """
    text_lower = text.lower()

    etc_cat = None
    for cat in categories:
        if cat["id"] == "etc":
            etc_cat = cat
            continue
        for kw in cat.get("keywords", []):
            if kw.lower() in text_lower:
                return cat["id"], cat["label"]

    # fallback: etc 카테고리 (없으면 마지막 항목)
    fallback = etc_cat or categories[-1]
    return fallback["id"], fallback["label"]

def extract_tags(text: str, categories: list, max_tags: int = 5) -> list:
    """매칭된 키워드 중 상위 max_tags개를 태그로 추출"""
    text_lower = text.lower()
    found = []
    for cat in categories:
        for kw in cat.get("keywords", []):
            if kw.lower() in text_lower:
                # 한국어/의미있는 짧은 키워드만 태그로
                if len(kw) >= 2 and kw not in found:
                    found.append(kw)
                if len(found) >= max_tags:
                    return found
    return found

# ── Notion 업로드 ─────────────────────────────────────────────────────
def push_to_notion(bookmark: dict) -> bool:
    """단일 북마크를 Notion DB에 업로드. 성공 시 True."""
    from urllib import request as ureq
    import urllib.error

    if not NOTION_TOKEN:
        print("  [SKIP] NOTION_TOKEN 환경변수 없음")
        return False

    title = (bookmark.get("text") or "")[:80].strip() or f"Tweet {bookmark['id']}"
    # 줄바꿈 제거
    title = title.replace("\n", " ").replace("\r", " ")

    properties = {
        "이름": {
            "title": [{"text": {"content": title}}]
        },
        "URL": {
            "url": bookmark.get("url") or None
        },
        "AuthorID": {
            "rich_text": [{"text": {"content": bookmark.get("authorHandle", "")}}]
        },
        "AuthorName": {
            "rich_text": [{"text": {"content": bookmark.get("authorName", "")}}]
        },
        "Category": {
            "select": {"name": bookmark.get("categoryLabel", "기타")}
        },
        "Text": {
            "rich_text": [{"text": {"content": (bookmark.get("text") or "")[:2000]}}]
        },
    }

    # Lang
    lang = bookmark.get("language")
    if lang:
        properties["Lang"] = {"select": {"name": lang}}

    # Media (첫 번째 이미지 URL)
    media = bookmark.get("media", [])
    if media and media[0]:
        properties["Media"] = {"url": media[0]}

    # Links (첫 번째 외부 링크)
    links = bookmark.get("links", [])
    if links and links[0]:
        properties["Links"] = {"url": links[0]}

    # TweetAt
    posted = bookmark.get("postedAt")
    if posted:
        try:
            from datetime import datetime
            # "Mon Jan 01 00:00:00 +0000 2024" 형식
            dt = datetime.strptime(posted, "%a %b %d %H:%M:%S +0000 %Y")
            properties["TweetAt"] = {"date": {"start": dt.strftime("%Y-%m-%d")}}
        except Exception:
            pass

    # SavedAt
    synced = bookmark.get("syncedAt")
    if synced:
        properties["SavedAt"] = {"date": {"start": synced[:10]}}

    # Tags (multi_select)
    tags = bookmark.get("tags", [])
    if tags:
        properties["Tags"] = {
            "multi_select": [{"name": t[:100]} for t in tags[:10]]
        }

    payload = json.dumps({
        "parent": {"database_id": NOTION_DB_ID},
        "properties": properties,
    }).encode("utf-8")

    req = ureq.Request(
        "https://api.notion.com/v1/pages",
        data=payload,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
        method="POST",
    )
    try:
        with ureq.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"  [ERROR] Notion HTTP {e.code}: {body[:200]}")
        return False
    except Exception as e:
        print(f"  [ERROR] Notion 오류: {e}")
        return False

# ── 메인 ─────────────────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  북마크 분류기")
    print("=" * 50)

    # 카테고리 로드
    categories = load_categories()
    print(f"카테고리 {len(categories)}개 로드: {[c['label'] for c in categories]}\n")

    # 이미 분류된 ID 로드
    already_done = set()
    if OUTPUT_FILE.exists() and not RESET_CLASSIFIED:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    already_done.add(json.loads(line)["id"])
                except Exception:
                    pass
        print(f"기존 분류 완료: {len(already_done)}개 (스킵됨)\n")

    # bookmarks.jsonl 읽기
    if not BOOKMARKS_FILE.exists():
        print(f"오류: {BOOKMARKS_FILE} 없음")
        print("bookmark_sync.py 먼저 실행하세요.")
        sys.exit(1)

    bookmarks = []
    with open(BOOKMARKS_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                bookmarks.append(json.loads(line.strip()))
            except Exception:
                pass

    print(f"전체 북마크: {len(bookmarks)}개")

    to_process = [b for b in bookmarks if b.get("id") not in already_done]
    print(f"분류 대상: {len(to_process)}개\n")

    if not to_process:
        if not RESET_CLASSIFIED:
            print("새로 분류할 북마크 없음.")
            print("재분류 하려면: python classify_bookmarks.py --reset")
            return
        # --reset: 전체 재분류
        print("(--reset 옵션: 전체 재분류 시작)")
        to_process = bookmarks
        already_done.clear()

    # 분류 실행
    stat = {}
    results = []

    for i, bm in enumerate(to_process, 1):
        text = (bm.get("text") or "") + " " + (bm.get("authorHandle") or "")
        cat_id, cat_label = classify(text, categories)
        tags = extract_tags(text, categories)

        bm_out = dict(bm)
        bm_out["categoryId"]    = cat_id
        bm_out["categoryLabel"] = cat_label
        bm_out["tags"]          = tags

        results.append(bm_out)
        stat[cat_label] = stat.get(cat_label, 0) + 1

        if i % 100 == 0:
            print(f"  {i}/{len(to_process)} 처리 중...")

    # 저장
    mode = "w" if RESET_CLASSIFIED else "a"
    with open(OUTPUT_FILE, mode, encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n분류 완료: {len(results)}개 → {OUTPUT_FILE.name}\n")
    print("카테고리별 통계:")
    for label, cnt in sorted(stat.items(), key=lambda x: -x[1]):
        bar = "█" * min(cnt // 5, 40)
        print(f"  {label:15s} {cnt:4d}개  {bar}")

    # Notion 업로드 (옵션)
    if NOTION_PUSH:
        print(f"\nNotion 업로드 시작...")
        import time
        success, fail = 0, 0
        for bm in results:
            ok = push_to_notion(bm)
            if ok:
                success += 1
            else:
                fail += 1
            time.sleep(0.35)  # Notion API rate limit

        print(f"Notion 업로드: 성공 {success}개 / 실패 {fail}개")

if __name__ == "__main__":
    main()
