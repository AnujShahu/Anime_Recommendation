import json
import urllib.request


ANILIST_API_URL = "https://graphql.anilist.co"


def search_anime(query=None, status=None, per_page=12, page=1):
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
            }
        )
    return results
