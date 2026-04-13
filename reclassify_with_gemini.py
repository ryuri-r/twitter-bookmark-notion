"""
reclassify_with_gemini.py
classified_bookmarks.jsonl에서 "기타" 항목만 Gemini로 재분류

사전 준비:
    $env:GEMINI_API_KEY="AIza..."

사용법:
    python reclassify_with_gemini.py
    python reclassify_with_gemini.py --dry-run   (실제 저장 없이 결과만 확인)
"""

import json, os, sys, time
from pathlib import Path
from urllib import request as ureq
import urllib.error

BASE_DIR         = Path(__file__).parent
CLASSIFIED_FILE  = BASE_DIR / "classified_bookmarks.jsonl"
CATEGORIES_FILE  = BASE_DIR / "categories.json"

# ── .env 자동 로드 ────────────────────────────────────────────────────
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL     = "gemini-2.5-flash"
BATCH_SIZE       = 10   # 한 번에 몇 개씩 보낼지
DRY_RUN          = "--dry-run" in sys.argv

def load_categories():
    with open(CATEGORIES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return [(c["id"], c["label"]) for c in data["categories"] if c["id"] != "etc"]

def build_prompt(tweets: list, categories: list) -> str:
    cat_list = "\n".join(f"- {cid}: {label}" for cid, label in categories)
    tweet_list = "\n".join(
        f'[{i+1}] {(t.get("text") or "")[:150].replace(chr(10), " ")}'
        for i, t in enumerate(tweets)
    )
    return f"""다음 트윗들을 아래 카테고리 중 하나로 분류해줘.
반드시 JSON 배열로만 응답해. 설명 없이 배열만.

카테고리:
{cat_list}
- etc: 기타 (위 어디에도 안 맞을 때만)

트윗:
{tweet_list}

응답 형식 (트윗 수와 동일한 개수):
["category_id", "category_id", ...]

예시: ["drawing", "fandom", "etc", "game"]

주의: 코드블록(```) 없이 JSON 배열만 반환해."""

def call_gemini(prompt: str) -> list:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY 환경변수 없음")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024}
    }).encode("utf-8")

    req = ureq.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with ureq.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        result = json.loads(raw)

    # 응답 구조 확인 (첫 배치만)
    if not hasattr(call_gemini, "_debugged"):
        call_gemini._debugged = True
        candidate = result.get("candidates", [{}])[0]
        print(f"\n[DEBUG] finishReason: {candidate.get('finishReason')}")
        parts = candidate.get("content", {}).get("parts", [])
        for i, p in enumerate(parts):
            print(f"[DEBUG] parts[{i}] keys: {list(p.keys())}")
            if "text" in p:
                print(f"[DEBUG] text[:200]: {p['text'][:200]}")

    candidate = result.get("candidates", [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    # text 필드가 있는 part 찾기 (thinking 모델은 thought 파트가 먼저 올 수 있음)
    text = ""
    for p in parts:
        if "text" in p and not p.get("thought", False):
            text = p["text"].strip()
            break

    if not text:
        raise ValueError(f"응답 비어있음. finishReason={candidate.get('finishReason')}, parts={[list(p.keys()) for p in parts]}")

    # JSON 배열 추출
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start == -1:
        raise ValueError(f"JSON 배열 없음. 응답: {text[:200]}")
    return json.loads(text[start:end])

def main():
    print("=" * 50)
    print("  Gemini 재분류기 (기타 항목)")
    print("=" * 50)

    if not GEMINI_API_KEY:
        print("\n오류: GEMINI_API_KEY 없음")
        print('설정: $env:GEMINI_API_KEY="AIza..."')
        sys.exit(1)

    categories = load_categories()
    cat_map = {cid: label for cid, label in categories}
    cat_map["etc"] = "기타"

    # classified_bookmarks 로드
    all_bookmarks = []
    with open(CLASSIFIED_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                all_bookmarks.append(json.loads(line.strip()))
            except:
                pass

    etc_items = [b for b in all_bookmarks if b.get("categoryId") == "etc"]
    print(f"전체: {len(all_bookmarks)}개 / 기타: {len(etc_items)}개\n")

    if not etc_items:
        print("재분류할 기타 항목 없음.")
        return

    if DRY_RUN:
        print("[DRY-RUN 모드: 저장 안 함]\n")

    # 배치 처리
    reclassified = {}
    total_batches = (len(etc_items) + BATCH_SIZE - 1) // BATCH_SIZE
    stat_before = {"etc": len(etc_items)}
    stat_after  = {}
    errors = 0

    for batch_idx in range(total_batches):
        batch = etc_items[batch_idx * BATCH_SIZE : (batch_idx + 1) * BATCH_SIZE]
        prompt = build_prompt(batch, categories)

        try:
            results = call_gemini(prompt)

            if len(results) != len(batch):
                print(f"  [배치 {batch_idx+1}] 응답 수 불일치 ({len(results)} != {len(batch)}) → 건너뜀")
                errors += 1
                continue

            for tweet, cat_id in zip(batch, results):
                cat_id = cat_id.strip()
                if cat_id not in cat_map:
                    cat_id = "etc"
                reclassified[tweet["id"]] = (cat_id, cat_map[cat_id])
                stat_after[cat_map[cat_id]] = stat_after.get(cat_map[cat_id], 0) + 1

            done = min((batch_idx + 1) * BATCH_SIZE, len(etc_items))
            print(f"  [{done}/{len(etc_items)}] 처리 완료...", end="\r")

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print(f"\n  [배치 {batch_idx+1}] HTTP {e.code}: {body[:100]}")
            errors += 1
            if e.code == 429:
                print("  Rate limit → 60초 대기")
                time.sleep(60)
        except Exception as e:
            print(f"\n  [배치 {batch_idx+1}] 오류: {e}")
            errors += 1

        time.sleep(0.5)  # Gemini 무료 15RPM 제한 여유

    print(f"\n\n재분류 완료: {len(reclassified)}개 / 오류: {errors}배치\n")

    # 통계
    print("재분류 결과:")
    for label, cnt in sorted(stat_after.items(), key=lambda x: -x[1]):
        print(f"  {label:15s} {cnt:4d}개")

    if DRY_RUN:
        print("\n[DRY-RUN] 저장 건너뜀.")
        return

    # classified_bookmarks.jsonl 업데이트
    updated = []
    changed = 0
    for bm in all_bookmarks:
        if bm["id"] in reclassified:
            cat_id, cat_label = reclassified[bm["id"]]
            if cat_id != "etc":
                bm["categoryId"]    = cat_id
                bm["categoryLabel"] = cat_label
                changed += 1
        updated.append(bm)

    with open(CLASSIFIED_FILE, "w", encoding="utf-8") as f:
        for bm in updated:
            f.write(json.dumps(bm, ensure_ascii=False) + "\n")

    print(f"\n저장 완료: {changed}개 업데이트 → {CLASSIFIED_FILE.name}")

    # 최종 통계
    final_stat = {}
    for bm in updated:
        lbl = bm.get("categoryLabel", "기타")
        final_stat[lbl] = final_stat.get(lbl, 0) + 1

    print("\n최종 카테고리별 통계:")
    for label, cnt in sorted(final_stat.items(), key=lambda x: -x[1]):
        bar = "█" * min(cnt // 5, 40)
        print(f"  {label:15s} {cnt:4d}개  {bar}")

if __name__ == "__main__":
    main()
