"""
reclassify_with_gemini.py
classified_bookmarks.jsonl에서 "기타" 항목만 AI로 재분류

지원 API (둘 중 하나만 있으면 됨, 둘 다 있으면 OpenAI 우선):
    - OpenAI:  .env에 OPENAI_API_KEY=sk-...       모델: gpt-4o-mini
    - Gemini:  .env에 GEMINI_API_KEY=AIza...       모델: gemini-2.0-flash

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
PROGRESS_FILE    = BASE_DIR / ".reclassify_progress.json"

# ── .env 자동 로드 ────────────────────────────────────────────────────
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# API 선택: OpenAI 우선, 없으면 Gemini
if OPENAI_API_KEY:
    AI_PROVIDER  = "openai"
    OPENAI_MODEL = "gpt-4.1-mini"
    BATCH_SIZE   = 20   # OpenAI는 빠르고 한도 여유로움
    SLEEP_SEC    = 1
elif GEMINI_API_KEY:
    AI_PROVIDER  = "gemini"
    GEMINI_MODEL = "gemini-2.5-flash"
    BATCH_SIZE   = 10   # 무료 15 RPM 기준
    SLEEP_SEC    = 4
else:
    AI_PROVIDER  = None
    BATCH_SIZE   = 10
    SLEEP_SEC    = 1

DRY_RUN = "--dry-run" in sys.argv


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

예시: ["drawing", "fandom", "etc", "tech"]

주의: 코드블록(```) 없이 JSON 배열만 반환해."""


def _http_post(url, payload_dict, headers):
    """공통 HTTP POST (429/503 재시도 포함)"""
    payload = json.dumps(payload_dict).encode("utf-8")
    retry_waits = [15, 30, 60]
    last_err = None
    for attempt in range(4):
        try:
            req = ureq.Request(url, data=payload, headers=headers, method="POST")
            with ureq.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 503) and attempt < 3:
                wait = retry_waits[attempt]
                print(f"\n  ⏳ HTTP {e.code} → {wait}초 후 재시도 ({attempt+1}/3)...")
                time.sleep(wait)
                continue
            raise
    raise last_err


def call_openai(prompt: str) -> list:
    result = _http_post(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 512,
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }
    )
    text = result["choices"][0]["message"]["content"].strip()
    start, end = text.find("["), text.rfind("]") + 1
    if start == -1:
        raise ValueError(f"JSON 배열 없음. 응답: {text[:200]}")
    return json.loads(text[start:end])


def call_gemini(prompt: str) -> list:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    result = _http_post(
        url,
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
        },
        {"Content-Type": "application/json"}
    )
    candidate = result.get("candidates", [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = ""
    for p in parts:
        if "text" in p and not p.get("thought", False):
            text = p["text"].strip()
            break
    if not text:
        raise ValueError(f"응답 비어있음. finishReason={candidate.get('finishReason')}")
    start, end = text.find("["), text.rfind("]") + 1
    if start == -1:
        raise ValueError(f"JSON 배열 없음. 응답: {text[:200]}")
    return json.loads(text[start:end])


def call_ai(prompt: str) -> list:
    if AI_PROVIDER == "openai":
        return call_openai(prompt)
    elif AI_PROVIDER == "gemini":
        return call_gemini(prompt)
    else:
        raise ValueError("API 키 없음")


def main():
    print("=" * 50)
    print("  AI 재분류기 (기타 항목)")
    print("=" * 50)

    if not AI_PROVIDER:
        print("\n⚠️  AI API 키가 없습니다.")
        print("  아래 중 하나를 .env 파일에 추가하세요:\n")
        print("  [OpenAI - 유료, 빠르고 안정적]")
        print("    OPENAI_API_KEY=sk-...")
        print("    발급: https://platform.openai.com/api-keys\n")
        print("  [Gemini - 무료 가능]")
        print("    GEMINI_API_KEY=AIza...")
        print("    발급: https://aistudio.google.com\n")
        print("  setup.bat을 다시 실행해서 키를 입력하거나,")
        print("  .env 파일을 직접 수정하세요.")
        sys.exit(1)

    provider_label = f"OpenAI ({OPENAI_MODEL})" if AI_PROVIDER == "openai" else f"Gemini ({GEMINI_MODEL})"
    print(f"  사용 API: {provider_label}\n")

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

    # 이전 진행분 로드 (중단 후 재실행 시 이어서)
    reclassified = {}
    if PROGRESS_FILE.exists() and not DRY_RUN:
        try:
            reclassified = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
            skip = sum(1 for item in etc_items if item["id"] in reclassified)
            if skip:
                print(f"  이전 진행분 {skip}개 로드됨 → 이어서 진행\n")
        except:
            pass

    # 배치 처리
    total_batches = (len(etc_items) + BATCH_SIZE - 1) // BATCH_SIZE
    stat_after = {}
    errors = 0

    for batch_idx in range(total_batches):
        batch = etc_items[batch_idx * BATCH_SIZE : (batch_idx + 1) * BATCH_SIZE]
        if all(item["id"] in reclassified for item in batch):
            continue

        prompt = build_prompt(batch, categories)

        try:
            results = call_ai(prompt)

            if len(results) != len(batch):
                print(f"  [배치 {batch_idx+1}] 응답 수 불일치 ({len(results)} != {len(batch)}) → 건너뜀")
                errors += 1
                continue

            for tweet, cat_id in zip(batch, results):
                cat_id = cat_id.strip()
                if cat_id not in cat_map:
                    cat_id = "etc"
                reclassified[tweet["id"]] = [cat_id, cat_map[cat_id]]
                stat_after[cat_map[cat_id]] = stat_after.get(cat_map[cat_id], 0) + 1

            if not DRY_RUN:
                PROGRESS_FILE.write_text(json.dumps(reclassified, ensure_ascii=False), encoding="utf-8")

            done = min((batch_idx + 1) * BATCH_SIZE, len(etc_items))
            print(f"  [{done}/{len(etc_items)}] 처리 완료...", end="\r")

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print(f"\n  [배치 {batch_idx+1}] HTTP {e.code}: {body[:120]}")
            errors += 1
            if e.code == 429:
                print("  ⏳ Rate limit → 60초 대기 후 계속...")
                time.sleep(60)
        except Exception as e:
            print(f"\n  [배치 {batch_idx+1}] 오류: {e}")
            errors += 1

        time.sleep(SLEEP_SEC)

    print(f"\n\n재분류 완료: {len(reclassified)}개 / 오류: {errors}배치\n")

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

    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()

    print(f"\n저장 완료: {changed}개 업데이트 → {CLASSIFIED_FILE.name}")

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
