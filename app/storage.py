"""
Lightweight storage for scraped posts (SQLite + JSONL dataset).
"""

import hashlib
import json
import os
import sqlite3
from datetime import datetime


_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(_BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "scraped_posts.db")
JSONL_PATH = os.path.join(DATA_DIR, "scraped_posts.jsonl")


def _ensure_storage() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            uid TEXT PRIMARY KEY,
            id TEXT,
            source TEXT,
            method TEXT,
            title TEXT,
            text TEXT,
            score INTEGER,
            created_utc TEXT,
            human_label TEXT,
            author TEXT,
            subreddit TEXT,
            url TEXT,
            num_comments INTEGER,
            scraped_at TEXT
        )
        """
    )
    return conn


def _post_uid(post: dict, source: str, method: str) -> str:
    post_id = str(post.get("id") or "").strip()
    if post_id:
        base = f"{source}:{method}:{post_id}"
    else:
        base = f"{source}:{method}:{post.get('title', '')}:{post.get('created_utc', '')}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def _append_jsonl(post: dict) -> None:
    with open(JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(post, ensure_ascii=True) + "\n")


def save_posts(posts: list, source: str | None = None, method: str | None = None) -> dict:
    """
    Persist scraped posts to SQLite + JSONL.
    Returns basic stats and storage paths.
    """
    if not posts:
        return {"inserted": 0, "total": 0, "db_path": DB_PATH, "jsonl_path": JSONL_PATH}

    conn = _ensure_storage()
    cur = conn.cursor()
    inserted = 0
    scraped_at = datetime.utcnow().isoformat()

    for post in posts:
        p_source = source or post.get("source") or "unknown"
        p_method = method or post.get("method") or "unknown"
        uid = _post_uid(post, p_source, p_method)

        row = (
            uid,
            str(post.get("id") or ""),
            p_source,
            p_method,
            post.get("title", ""),
            post.get("text", ""),
            int(post.get("score") or 0),
            str(post.get("created_utc") or ""),
            post.get("human_label"),
            post.get("author"),
            post.get("subreddit"),
            post.get("url"),
            int(post.get("num_comments")) if post.get("num_comments") is not None else None,
            scraped_at,
        )

        cur.execute(
            """
            INSERT OR IGNORE INTO posts (
                uid, id, source, method, title, text, score, created_utc,
                human_label, author, subreddit, url, num_comments, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )

        if cur.rowcount == 1:
            inserted += 1
            _append_jsonl(
                {
                    "uid": uid,
                    "id": row[1],
                    "source": row[2],
                    "method": row[3],
                    "title": row[4],
                    "text": row[5],
                    "score": row[6],
                    "created_utc": row[7],
                    "human_label": row[8],
                    "author": row[9],
                    "subreddit": row[10],
                    "url": row[11],
                    "num_comments": row[12],
                    "scraped_at": row[13],
                }
            )

    conn.commit()
    conn.close()

    return {"inserted": inserted, "total": len(posts), "db_path": DB_PATH, "jsonl_path": JSONL_PATH}


def get_all_posts(source: str | None = None, method: str | None = None, limit: int | None = None) -> list[dict]:
    """Retrieve all posts from the database with optional filtering."""
    conn = _ensure_storage()
    cur = conn.cursor()
    
    query = "SELECT * FROM posts WHERE 1=1"
    params = []
    
    if source:
        query += " AND source = ?"
        params.append(source)
    
    if method:
        query += " AND method = ?"
        params.append(method)
    
    query += " ORDER BY scraped_at DESC"
    
    if limit:
        query += f" LIMIT {limit}"
    
    cur.execute(query, params)
    columns = [desc[0] for desc in cur.description]
    posts = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    conn.close()
    return posts


def export_to_csv(filename: str | None = None, source: str | None = None, method: str | None = None) -> str:
    """Export posts to CSV file."""
    import csv
    
    posts = get_all_posts(source=source, method=method)
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{source}" if source else ""
        suffix += f"_{method}" if method else ""
        filename = f"scrapes{suffix}_{timestamp}.csv"
    
    export_path = os.path.join(DATA_DIR, "exports", filename)
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    
    if not posts:
        return export_path
    
    with open(export_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=posts[0].keys())
        writer.writeheader()
        writer.writerows(posts)
    
    return export_path


def export_to_json(filename: str | None = None, source: str | None = None, method: str | None = None) -> str:
    """Export posts to JSON file."""
    posts = get_all_posts(source=source, method=method)
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{source}" if source else ""
        suffix += f"_{method}" if method else ""
        filename = f"scrapes{suffix}_{timestamp}.json"
    
    export_path = os.path.join(DATA_DIR, "exports", filename)
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    
    return export_path


def get_stats() -> dict:
    """Get statistics about stored posts."""
    conn = _ensure_storage()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM posts")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT source, method, COUNT(*) as count FROM posts GROUP BY source, method")
    by_source_method = [{"source": row[0], "method": row[1], "count": row[2]} for row in cur.fetchall()]
    
    cur.execute("SELECT MIN(scraped_at), MAX(scraped_at) FROM posts")
    dates = cur.fetchone()
    
    conn.close()
    
    return {
        "total_posts": total,
        "by_source_method": by_source_method,
        "first_scrape": dates[0],
        "last_scrape": dates[1],
        "db_path": DB_PATH,
        "jsonl_path": JSONL_PATH
    }
