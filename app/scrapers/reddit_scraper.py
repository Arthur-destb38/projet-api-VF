"""
Reddit Scraper - HTTP/JSON
"""

import requests
import time


def scrape_reddit(subreddit: str, limit: int = 100, max_limit: int = 1000) -> list:
    posts = []
    after = None
    headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"}

    limit = min(limit, max_limit)

    while len(posts) < limit:
        url = f"https://old.reddit.com/r/{subreddit}/new.json"
        params = {"limit": min(100, limit - len(posts))}
        if after:
            params["after"] = after

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            data = resp.json()
        except Exception as e:
            print(f"Erreur Reddit: {e}")
            break

        children = data.get("data", {}).get("children", [])
        if not children:
            break

        for child in children:
            d = child.get("data", {})
            posts.append({
                "id": d.get("id"),
                "title": d.get("title", ""),
                "text": d.get("selftext", ""),
                "score": d.get("score", 0),
                "created_utc": d.get("created_utc"),
                "source": "reddit",
                "human_label": None
            })
            if len(posts) >= limit:
                break

        after = data.get("data", {}).get("after")
        if not after:
            break

        time.sleep(0.3)

    return posts