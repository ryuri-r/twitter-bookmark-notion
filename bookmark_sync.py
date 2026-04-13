"""
bookmark_sync.py
Twitter GraphQL API로 북마크 직접 동기화
저장: 이 스크립트와 같은 폴더 내 bookmarks.jsonl
"""
import json, os, sys, time
from pathlib import Path
from urllib import request, parse

FORCE_FULL = "--force" in sys.argv  # 이미 있는 것 나와도 끝까지 수집

# ── .env 자동 로드 ────────────────────────────────────────────────────
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ── 설정 ────────────────────────────────────────────────────────────
OUTPUT_DIR   = Path(__file__).parent          # 스크립트와 같은 폴더
OUTPUT_FILE  = OUTPUT_DIR / "bookmarks.jsonl"

# 트위터 인증 정보 (.env에서 로드)
_CT0        = os.environ.get("TWITTER_CT0", "")
_AUTH_TOKEN = os.environ.get("TWITTER_AUTH_TOKEN", "")

BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
QUERY_ID  = "Z9GWmP0kP2dajyckAaDUBw"
FEATURES  = {
    "graphql_timeline_v2_bookmark_timeline": True,
    "rweb_tipjar_consumption_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "articles_preview_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "tweetypie_unmention_optimization_enabled": True,
    "responsive_web_uc_gql_enabled": True,
    "vibe_api_enabled": True,
    "responsive_web_text_conversations_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "responsive_web_media_download_video_enabled": False,
}

def _best_media_url(m: dict) -> str:
    """
    미디어 항목에서 실제 원본 URL 반환.
    - photo       → media_url_https?format=jpg&name=orig (원본 해상도)
    - video       → video_info.variants 중 최고 bitrate MP4
    - animated_gif→ video_info.variants MP4 (트위터가 gif→mp4 변환)
    """
    mtype = m.get("type", "photo")
    if mtype == "photo":
        base = m.get("media_url_https", "")
        if base:
            # 트위터 이미지 원본: ?format=jpg&name=orig
            base = base.split("?")[0]
            return base + "?format=jpg&name=orig"
        return ""
    elif mtype in ("video", "animated_gif"):
        variants = (m.get("video_info") or {}).get("variants", [])
        # MP4만, bitrate 높은 순
        mp4s = [v for v in variants if v.get("content_type") == "video/mp4" and v.get("url")]
        if mp4s:
            best = max(mp4s, key=lambda v: v.get("bitrate", 0))
            return best["url"]
        # fallback: 썸네일
        return m.get("media_url_https", "")
    return m.get("media_url_https", "")


def load_cookies():
    if not _CT0 or not _AUTH_TOKEN:
        print("오류: 트위터 토큰이 설정되지 않았습니다.")
        print("setup.bat을 실행해서 토큰을 먼저 입력해주세요.")
        sys.exit(1)
    return {"ct0": _CT0, "auth_token": _AUTH_TOKEN}

def fetch_bookmarks_page(ct0, auth_token, cursor=None):
    variables = {"count": 20, "includePromotedContent": False}
    if cursor:
        variables["cursor"] = cursor

    params = parse.urlencode({
        "variables": json.dumps(variables),
        "features":  json.dumps(FEATURES),
    })
    url = f"https://x.com/i/api/graphql/{QUERY_ID}/Bookmarks?{params}"

    cookie_header = f"ct0={ct0}; auth_token={auth_token}"
    req = request.Request(url, headers={
        "Authorization":         f"Bearer {BEARER}",
        "Cookie":                cookie_header,
        "x-csrf-token":          ct0,
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type":   "OAuth2Session",
        "User-Agent":            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0.0.0 Safari/537.36",
        "Accept":                "application/json",
        "Referer":               "https://x.com/i/bookmarks",
        "Accept-Language":       "ko,en;q=0.9",
    })
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def extract_entries(data):
    """응답에서 트윗 목록과 다음 커서 추출"""
    tweets  = []
    cursor  = None
    try:
        timeline = data["data"]["bookmark_timeline_v2"]["timeline"]
        for inst in timeline.get("instructions", []):
            for entry in inst.get("entries", []):
                eid = entry.get("entryId", "")
                content = entry.get("content", {})

                # 커서
                if "cursor-bottom" in eid:
                    cursor = content.get("value")
                    continue

                # 트윗
                result = (content.get("itemContent", {})
                                 .get("tweet_results", {})
                                 .get("result", {}))
                if not result:
                    continue

                # 신규 구조: TweetWithVisibilityResults → result["tweet"] 한 단계 더
                tweet_obj = result.get("tweet", result)

                core   = tweet_obj.get("core", {})
                legacy = tweet_obj.get("legacy", {})

                user_result = (core.get("user_results", {})
                                   .get("result", {}))
                # name/screen_name: 신규는 user.core, 구버전은 user.legacy
                user_core   = user_result.get("core", {})
                user_legacy = user_result.get("legacy", {})
                screen_name = user_core.get("screen_name") or user_legacy.get("screen_name", "")
                author_name = user_core.get("name") or user_legacy.get("name", "")

                media_list = (legacy.get("extended_entities") or
                              legacy.get("entities") or {}).get("media", [])

                tweet_id = legacy.get("id_str") or tweet_obj.get("rest_id", "") or result.get("rest_id", "")

                record = {
                    "id":              tweet_id,
                    "tweetId":         tweet_id,
                    "url":             f"https://x.com/{screen_name}/status/{tweet_id}",
                    "text":            legacy.get("full_text", ""),
                    "authorHandle":    screen_name,
                    "authorName":      author_name,
                    "postedAt":        legacy.get("created_at"),
                    "bookmarkedAt":    None,
                    "syncedAt":        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "language":        legacy.get("lang"),
                    "possiblySensitive": legacy.get("possibly_sensitive", False),
                    "engagement": {
                        "likeCount":     legacy.get("favorite_count", 0),
                        "repostCount":   legacy.get("retweet_count", 0),
                        "replyCount":    legacy.get("reply_count", 0),
                        "bookmarkCount": legacy.get("bookmark_count", 0),
                    },
                    "media": [_best_media_url(m) for m in media_list if _best_media_url(m)],
                    "mediaObjects": [
                        {
                            "mediaUrl":   _best_media_url(m),
                            "previewUrl": m.get("media_url_https"),
                            "type":       m.get("type"),
                            "width":      m.get("original_info", {}).get("width"),
                            "height":     m.get("original_info", {}).get("height"),
                        }
                        for m in media_list
                    ],
                    "links": [u.get("expanded_url") for u in
                              (legacy.get("entities", {}).get("urls") or [])
                              if u.get("expanded_url") and "t.co" not in u.get("expanded_url","")],
                    "tags":   [],
                    "ingestedVia": "graphql-python",
                }
                tweets.append(record)
    except (KeyError, TypeError) as e:
        print(f"  파싱 오류: {e}")

    return tweets, cursor

def sync():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cookies   = load_cookies()
    ct0       = cookies["ct0"]
    auth_token = cookies["auth_token"]

    # 기존 북마크 ID 로드 (중복 방지)
    existing_ids = set()
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    existing_ids.add(json.loads(line)["id"])
                except Exception:
                    pass

    print(f"기존 북마크: {len(existing_ids)}개")

    all_new   = []
    cursor    = None
    page      = 0
    max_pages = 500

    while page < max_pages:
        page += 1
        print(f"  페이지 {page} 가져오는 중...", end=" ", flush=True)

        try:
            data   = fetch_bookmarks_page(ct0, auth_token, cursor)
            tweets, cursor = extract_entries(data)
        except Exception as e:
            print(f"오류: {e}")
            break

        new_tweets = [t for t in tweets if t["id"] not in existing_ids]
        all_new.extend(new_tweets)
        for t in new_tweets:
            existing_ids.add(t["id"])

        print(f"{len(tweets)}개 수신, {len(new_tweets)}개 신규")

        if not tweets or not cursor:
            print("  마지막 페이지 도달")
            break

        if len(new_tweets) == 0 and not FORCE_FULL:
            # 이미 있는 것만 나오면 중단 (증분 모드)
            print("  모두 기존 북마크 → 완료")
            break

        time.sleep(0.6)

    # 저장
    if all_new:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for t in all_new:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        print(f"\n신규 저장: {len(all_new)}개")
    else:
        print("\n신규 북마크 없음")

    print(f"파일 위치: {OUTPUT_FILE}")
    print(f"전체 북마크: {len(existing_ids)}개")
    return len(all_new)

if __name__ == "__main__":
    print("=" * 45)
    print("  Twitter 북마크 동기화 (직접 API)")
    print("=" * 45)
    sync()
