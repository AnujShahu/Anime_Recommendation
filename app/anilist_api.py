import json
import urllib.request
import urllib.error
import urllib.parse


ANILIST_API_URL = "https://graphql.anilist.co"
JIKAN_API_URL = "https://api.jikan.moe/v4/anime"


def _jikan_status(status):
    status_map = {
        "AIRING": "airing",
        "FINISHED": "complete",
        "NOT_YET_RELEASED": "upcoming",
    }
    return status_map.get(status)


def check_anilist_health():
    gql = """
    query {
      Page(page: 1, perPage: 1) {
        media(type: ANIME, search: "Naruto") {
          id
          title { romaji english }
        }
      }
    }
    """

    payload = json.dumps({"query": gql}).encode("utf-8")
    req = urllib.request.Request(
        ANILIST_API_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            media = data.get("data", {}).get("Page", {}).get("media", [])
            return {
                "ok": bool(media),
                "source": "AniList",
                "status_code": response.status,
                "sample_count": len(media),
                "message": "AniList API is reachable." if media else "AniList responded, but no sample data returned.",
            }
    except urllib.error.HTTPError as error:
        return {
            "ok": False,
            "source": "AniList",
            "status_code": error.code,
            "sample_count": 0,
            "message": f"AniList returned HTTP {error.code}.",
        }
    except Exception as error:
        return {
            "ok": False,
            "source": "AniList",
            "status_code": None,
            "sample_count": 0,
            "message": str(error),
        }


def check_jikan_health():
    params = urllib.parse.urlencode({"q": "Naruto", "limit": 1})
    req = urllib.request.Request(
        f"{JIKAN_API_URL}?{params}",
        headers={"Accept": "application/json", "User-Agent": "AnimeRecommendation/1.0"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            media = data.get("data", [])
            return {
                "ok": bool(media),
                "source": "Jikan",
                "status_code": response.status,
                "sample_count": len(media),
                "message": "Jikan API is reachable." if media else "Jikan responded, but no sample data returned.",
            }
    except urllib.error.HTTPError as error:
        return {
            "ok": False,
            "source": "Jikan",
            "status_code": error.code,
            "sample_count": 0,
            "message": f"Jikan returned HTTP {error.code}.",
        }
    except Exception as error:
        return {
            "ok": False,
            "source": "Jikan",
            "status_code": None,
            "sample_count": 0,
            "message": str(error),
        }


def check_live_api_health():
    anilist = check_anilist_health()
    jikan = check_jikan_health()
    working_sources = [item["source"] for item in (anilist, jikan) if item["ok"]]

    return {
        "ok": bool(working_sources),
        "primary": "AniList",
        "fallback": "Jikan",
        "working_sources": working_sources,
        "sources": {
            "anilist": anilist,
            "jikan": jikan,
        },
        "message": "Live anime APIs are reachable." if working_sources else "No live anime API is reachable.",
    }


def _search_anilist(query=None, status=None, per_page=12, page=1):
    gql = """
    query ($search: String, $status: MediaStatus, $page: Int, $perPage: Int) {
      Page(page: $page, perPage: $perPage) {
        media(type: ANIME, search: $search, status: $status, sort: POPULARITY_DESC) {
          id
          title { romaji english }
          genres
          averageScore
          episodes
          status
          season
          seasonYear
          coverImage { large }
        }
      }
    }
    """

    variables = {
        "search": query if query else None,
        "status": status if status else None,
        "page": page,
        "perPage": per_page,
    }

    payload = json.dumps({"query": gql, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        ANILIST_API_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
    except Exception:
        return []

    media = data.get("data", {}).get("Page", {}).get("media", [])
    results = []
    for item in media:
        title_obj = item.get("title") or {}
        title = title_obj.get("english") or title_obj.get("romaji") or "Unknown"
        results.append(
            {
                "external_id": item.get("id"),
                "title": title,
                "genres": ", ".join(item.get("genres") or []),
                "image_url": (item.get("coverImage") or {}).get("large"),
                "score": item.get("averageScore"),
                "episodes": item.get("episodes"),
                "status": item.get("status"),
                "season": item.get("season"),
                "seasonYear": item.get("seasonYear"),
                "source": "AniList",
            }
        )
    return results


def _search_jikan(query=None, status=None, per_page=12, page=1):
    params = {
        "limit": per_page,
        "page": page,
        "order_by": "popularity",
        "sort": "asc",
    }

    if query:
        params["q"] = query

    mapped_status = _jikan_status(status)
    if mapped_status:
        params["status"] = mapped_status

    query_string = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{JIKAN_API_URL}?{query_string}",
        headers={"Accept": "application/json", "User-Agent": "AnimeRecommendation/1.0"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
    except Exception:
        return []

    results = []
    for item in data.get("data", []):
        title = item.get("title_english") or item.get("title") or "Unknown"
        images = item.get("images") or {}
        jpg = images.get("jpg") or {}
        genres = [genre.get("name") for genre in item.get("genres", []) if genre.get("name")]

        results.append(
            {
                "external_id": item.get("mal_id"),
                "title": title,
                "genres": ", ".join(genres),
                "image_url": jpg.get("large_image_url") or jpg.get("image_url"),
                "score": item.get("score"),
                "episodes": item.get("episodes"),
                "status": item.get("status"),
                "season": item.get("season"),
                "seasonYear": item.get("year"),
                "source": "Jikan",
            }
        )

    return results


def search_anime(query=None, status=None, per_page=12, page=1):
    anilist_results = _search_anilist(query=query, status=status, per_page=per_page, page=page)
    if anilist_results:
        return anilist_results

    return _search_jikan(query=query, status=status, per_page=per_page, page=page)
