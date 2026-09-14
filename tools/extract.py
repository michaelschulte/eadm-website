"""Pulls curated WordPress content out of the scratch MariaDB import as
JSON. Uses JSON_ARRAYAGG(JSON_OBJECT(...)) so MySQL itself handles all
string escaping -- far more robust than parsing the raw SQL dump by hand.

Must invoke the mysql CLI with -r (raw mode): plain -N -B batch output
double-escapes backslashes inside the JSON text and corrupts it (verified
during design).
"""

import json
import subprocess
from pathlib import Path

CONTAINER = "eadm_mysql_import"
OUT_DIR = Path(__file__).parent / "_extracted"

QUERIES = {
    "pages.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'id', ID, 'type', post_type, 'title', post_title,
            'slug', post_name, 'date', post_date, 'content', post_content
        )) FROM SERVMASK_PREFIX_posts
        WHERE post_status = 'publish' AND post_type = 'page';
    """,
    "posts.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'id', ID, 'type', post_type, 'title', post_title,
            'slug', post_name, 'date', post_date, 'content', post_content
        )) FROM SERVMASK_PREFIX_posts
        WHERE post_status = 'publish' AND post_type = 'post';
    """,
    "categories.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT('post_id', p.ID, 'category', t.name))
        FROM SERVMASK_PREFIX_posts p
        JOIN SERVMASK_PREFIX_term_relationships tr ON tr.object_id = p.ID
        JOIN SERVMASK_PREFIX_term_taxonomy tt
            ON tt.term_taxonomy_id = tr.term_taxonomy_id AND tt.taxonomy = 'category'
        JOIN SERVMASK_PREFIX_terms t ON t.term_id = tt.term_id
        WHERE p.post_status = 'publish' AND p.post_type = 'post';
    """,
    "attachments.json": """
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'id', p.ID,
            'file', (SELECT meta_value FROM SERVMASK_PREFIX_postmeta pm
                     WHERE pm.post_id = p.ID AND pm.meta_key = '_wp_attached_file'
                     LIMIT 1)
        )) FROM SERVMASK_PREFIX_posts p WHERE p.post_type = 'attachment';
    """,
}


def run_query(sql: str) -> list:
    full_sql = "SET SESSION group_concat_max_len = 1000000000;\n" + sql
    result = subprocess.run(
        ["docker", "exec", "-i", CONTAINER, "mysql", "-uroot", "-proot", "-N", "-B", "-r", "eadm"],
        input=full_sql,
        capture_output=True,
        text=True,
        check=True,
    )
    raw = result.stdout.strip()
    return json.loads(raw) if raw else []


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for filename, sql in QUERIES.items():
        data = run_query(sql)
        # Normalize WordPress's Windows-style line endings.
        for row in data:
            if "content" in row and row["content"] is not None:
                row["content"] = row["content"].replace("\r\n", "\n")
        (OUT_DIR / filename).write_text(json.dumps(data, indent=2))
        print(f"{filename}: {len(data)} rows")


if __name__ == "__main__":
    main()
