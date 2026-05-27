from __future__ import annotations

from app.core.supabase_client import SupabaseError, eq, rest_insert, rest_select


POST_COLUMNS = "id,alumni_id,post_type,title,description,company,apply_url,expires_at,created_at"


def list_alumni_posts(post_type: str = "") -> list[dict]:
    query = {"select": POST_COLUMNS, "order": "created_at.desc"}
    if post_type:
        query["post_type"] = eq(post_type)
    try:
        return rest_select("alumni_posts", query)
    except SupabaseError:
        return []


def create_alumni_post(
    *,
    alumni_id: str,
    post_type: str,
    title: str,
    description: str,
    company: str,
    apply_url: str,
    expires_at: str,
) -> tuple[bool, str]:
    if post_type not in {"job", "internship", "guidance"}:
        return False, "Invalid post type."
    if not title.strip():
        return False, "Title is required."
    try:
        rest_insert(
            "alumni_posts",
            {
                "alumni_id": alumni_id,
                "post_type": post_type,
                "title": title.strip(),
                "description": description.strip() or None,
                "company": company.strip() or None,
                "apply_url": apply_url.strip() or None,
                "expires_at": expires_at.strip() or None,
            },
        )
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Post created successfully."


def count_posts_by_type() -> dict[str, int]:
    counts = {"job": 0, "internship": 0, "guidance": 0}
    for post in list_alumni_posts():
        post_type = post.get("post_type")
        if post_type in counts:
            counts[post_type] += 1
    return counts
