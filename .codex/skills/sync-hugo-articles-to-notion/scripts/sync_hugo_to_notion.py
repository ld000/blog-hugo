#!/usr/bin/env python3
"""Sync Hugo Markdown articles into a Notion articles data source/database."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback is tested by dry-run usage.
    yaml = None


DEFAULT_PROPERTY_MAP = {
    "title": "Name",
    "slug": "Slug",
    "source_path": "Source Path",
    "section": "Section",
    "date": "Date",
    "tags": "Tags",
    "categories": "Categories",
    "series": "Series",
    "description": "Description",
    "draft": "Draft",
    "url": "URL",
    "last_synced": "Last Synced",
    "content_hash": "Content Hash",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Hugo repository root")
    parser.add_argument("--config", default=".codex/notion-article-sync.json")
    parser.add_argument("--token", default=os.environ.get("NOTION_TOKEN"))
    parser.add_argument("--data-source-id", default=os.environ.get("NOTION_DATA_SOURCE_ID"))
    parser.add_argument("--database-id", default=os.environ.get("NOTION_DATABASE_ID"))
    parser.add_argument("--notion-version", default=os.environ.get("NOTION_VERSION", "2026-03-11"))
    parser.add_argument("--site-url", default=None, help="Canonical site URL for article links")
    parser.add_argument("--content-mode", choices=["none", "full"], default="none")
    parser.add_argument("--image-mode", choices=["upload", "external", "text"], default=os.environ.get("NOTION_IMAGE_MODE", "upload"))
    parser.add_argument("--include-drafts", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--slug", action="append", default=[], help="Sync only matching slug(s)")
    parser.add_argument("--force", action="store_true", help="Update even when Content Hash matches")
    return parser.parse_args()


def load_config(repo: Path, config_path: str) -> dict[str, Any]:
    path = Path(config_path)
    if not path.is_absolute():
        path = repo / path
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def simple_yaml_value(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "Null", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [simple_yaml_value(part.strip()) for part in inner.split(",")]
    if re.match(r"^\d{4}-\d{2}-\d{2}", value):
        return value
    return value


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text
    raw = parts[1]
    body = parts[2]
    if yaml is not None:
        data = yaml.safe_load(raw) or {}
        return dict(data), body

    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = simple_yaml_value(value)
    return data, body


def discover_articles(repo: Path, config: dict[str, Any], include_drafts: bool) -> list[dict[str, Any]]:
    content_dirs = config.get("content_dirs") or ["content/ai", "content/posts", "content/springweek"]
    articles: list[dict[str, Any]] = []
    for configured_dir in content_dirs:
        base = repo / configured_dir
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if path.name == "_index.md":
                continue
            raw = path.read_text(encoding="utf-8")
            front_matter, body = parse_front_matter(raw)
            if front_matter.get("draft") is True and not include_drafts:
                continue
            rel = path.relative_to(repo).as_posix()
            parts = Path(rel).parts
            section = parts[1] if len(parts) > 2 and parts[0] == "content" else ""
            slug = path.parent.name if path.name == "index.md" else path.stem
            title = str(front_matter.get("title") or slug)
            source_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            articles.append(
                {
                    "front_matter": front_matter,
                    "body": body,
                    "title": title,
                    "section": section,
                    "slug": slug,
                    "path": path,
                    "article_dir": path.parent,
                    "source_path": rel,
                    "content_hash": source_hash,
                }
            )
    return articles


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def iso_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def article_url(site_url: str | None, article: dict[str, Any]) -> str | None:
    if not site_url:
        return None
    base = site_url.rstrip("/") + "/"
    section = article["section"].strip("/")
    slug = article["slug"].strip("/")
    return urllib.parse.urljoin(base, f"{section}/{slug}/")


class NotionClient:
    def __init__(self, token: str, version: str, use_data_source: bool):
        self.token = token
        self.version = version
        self.use_data_source = use_data_source

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.notion.com/v1{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Notion-Version": self.version,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Notion API {method} {path} failed: {exc.code} {message}") from exc

    def upload_file(self, file_path: Path) -> str:
        print(f"Uploading image: {file_path}", file=sys.stderr, flush=True)
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        created = self.request(
            "POST",
            "/file_uploads",
            {
                "mode": "single_part",
                "filename": file_path.name,
                "content_type": content_type,
            },
        )
        upload_id = created["id"]
        return self.send_file_upload(upload_id, file_path, content_type)["id"]

    def send_file_upload(self, upload_id: str, file_path: Path, content_type: str) -> dict[str, Any]:
        boundary = f"----codex-notion-{os.urandom(12).hex()}"
        file_bytes = file_path.read_bytes()
        body = b"".join(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode("utf-8"),
                f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
                file_bytes,
                f"\r\n--{boundary}--\r\n".encode("utf-8"),
            ]
        )
        request = urllib.request.Request(
            f"https://api.notion.com/v1/file_uploads/{upload_id}/send",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Notion-Version": self.version,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Notion API file upload failed for {file_path}: {exc.code} {message}") from exc

    def get_container(self, container_id: str) -> dict[str, Any]:
        if self.use_data_source:
            return self.request("GET", f"/data_sources/{container_id}")
        return self.request("GET", f"/databases/{container_id}")

    def query_pages(self, container_id: str) -> list[dict[str, Any]]:
        endpoint = f"/data_sources/{container_id}/query" if self.use_data_source else f"/databases/{container_id}/query"
        pages: list[dict[str, Any]] = []
        payload: dict[str, Any] = {"page_size": 100}
        while True:
            response = self.request("POST", endpoint, payload)
            pages.extend(response.get("results", []))
            if not response.get("has_more"):
                return pages
            payload["start_cursor"] = response.get("next_cursor")

    def create_page(self, container_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        if self.use_data_source:
            parent: dict[str, Any] = {"type": "data_source_id", "data_source_id": container_id}
        else:
            parent = {"type": "database_id", "database_id": container_id}
        return self.request("POST", "/pages", {"parent": parent, "properties": properties})

    def update_page(self, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/pages/{page_id}", {"properties": properties})

    def replace_children(self, page_id: str, blocks: list[dict[str, Any]]) -> None:
        existing = self.list_children(page_id)
        print(f"Replacing page body: deleting {len(existing)} existing blocks", file=sys.stderr, flush=True)
        for index, block in enumerate(existing, start=1):
            self.request("DELETE", f"/blocks/{block['id']}")
            if index % 25 == 0:
                print(f"Deleted {index}/{len(existing)} blocks", file=sys.stderr, flush=True)
        for index in range(0, len(blocks), 100):
            print(f"Appending blocks {index + 1}-{min(index + 100, len(blocks))}/{len(blocks)}", file=sys.stderr, flush=True)
            self.request("PATCH", f"/blocks/{page_id}/children", {"children": blocks[index : index + 100]})

    def list_children(self, block_id: str) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        cursor = None
        while True:
            query = f"?start_cursor={cursor}" if cursor else ""
            response = self.request("GET", f"/blocks/{block_id}/children{query}")
            blocks.extend(response.get("results", []))
            if not response.get("has_more"):
                return blocks
            cursor = response.get("next_cursor")


def schema_properties(container: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return container.get("properties", {})


def find_title_property(schema: dict[str, dict[str, Any]], property_map: dict[str, str]) -> str:
    configured = property_map.get("title")
    if configured in schema and schema[configured].get("type") == "title":
        return configured
    for name, meta in schema.items():
        if meta.get("type") == "title":
            return name
    return configured or "Name"


def rich_text(text: str, max_len: int = 2000) -> list[dict[str, Any]]:
    if not text:
        return []
    return [{"type": "text", "text": {"content": text[index : index + max_len]}} for index in range(0, len(text), max_len)]


def notion_properties(
    article: dict[str, Any],
    schema: dict[str, dict[str, Any]],
    property_map: dict[str, str],
    site_url: str | None,
) -> dict[str, Any]:
    fm = article["front_matter"]
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    values = {
        "title": article["title"],
        "slug": article["slug"],
        "source_path": article["source_path"],
        "section": article["section"],
        "date": iso_date(fm.get("date")),
        "tags": as_list(fm.get("tags")),
        "categories": as_list(fm.get("categories")),
        "series": as_list(fm.get("series")),
        "description": str(fm.get("description") or ""),
        "draft": bool(fm.get("draft", False)),
        "url": article_url(site_url, article),
        "last_synced": now,
        "content_hash": article["content_hash"],
    }

    props: dict[str, Any] = {}
    title_prop = find_title_property(schema, property_map)
    props[title_prop] = {"title": rich_text(values["title"])}

    for key, prop_name in property_map.items():
        if key == "title" or prop_name not in schema:
            continue
        prop_type = schema[prop_name].get("type")
        value = values.get(key)
        if prop_type == "rich_text" and value is not None:
            props[prop_name] = {"rich_text": rich_text(str(value))}
        elif prop_type == "select" and value:
            props[prop_name] = {"select": {"name": str(value)}}
        elif prop_type == "multi_select":
            props[prop_name] = {"multi_select": [{"name": item} for item in as_list(value)]}
        elif prop_type == "date" and value:
            props[prop_name] = {"date": {"start": str(value)}}
        elif prop_type == "checkbox":
            props[prop_name] = {"checkbox": bool(value)}
        elif prop_type == "url" and value:
            props[prop_name] = {"url": str(value)}
    return props


def extract_plain_property(page: dict[str, Any], prop_name: str) -> str:
    prop = page.get("properties", {}).get(prop_name) or {}
    prop_type = prop.get("type")
    if prop_type in {"rich_text", "title"}:
        return "".join(item.get("plain_text", "") for item in prop.get(prop_type, []))
    if prop_type == "url":
        return prop.get("url") or ""
    return ""


def page_index(pages: list[dict[str, Any]], property_map: dict[str, str]) -> dict[str, dict[str, dict[str, Any]]]:
    by_source: dict[str, dict[str, Any]] = {}
    by_slug: dict[str, dict[str, Any]] = {}
    by_title: dict[str, dict[str, Any]] = {}
    for page in pages:
        source = extract_plain_property(page, property_map["source_path"])
        slug = extract_plain_property(page, property_map["slug"])
        title = extract_plain_property(page, property_map["title"])
        if source:
            by_source[source] = page
        if slug:
            by_slug[slug] = page
        if title:
            by_title[title] = page
    return {"source": by_source, "slug": by_slug, "title": by_title}


def matching_page(article: dict[str, Any], pages: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any] | None:
    return (
        pages["source"].get(article["source_path"])
        or pages["slug"].get(article["slug"])
        or pages["title"].get(article["title"])
    )


def asset_url(site_url: str | None, article: dict[str, Any], image_src: str) -> str | None:
    page_url = article_url(site_url, article)
    if not page_url:
        return None
    return urllib.parse.urljoin(page_url, image_src)


def image_block_from_upload(upload_id: str, caption: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "file_upload",
            "file_upload": {"id": upload_id},
            "caption": rich_text(caption),
        },
    }


def image_block_from_external(url: str, caption: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": url},
            "caption": rich_text(caption),
        },
    }


def notion_code_language(language: str) -> str:
    normalized = language.strip().lower()
    if normalized in {"", "txt", "text", "plaintext"}:
        return "plain text"
    return normalized


def markdown_blocks(
    markdown: str,
    *,
    article: dict[str, Any] | None = None,
    client: NotionClient | None = None,
    image_mode: str = "upload",
    site_url: str | None = None,
) -> list[dict[str, Any]]:
    lines = markdown.splitlines()
    blocks: list[dict[str, Any]] = []
    paragraph: list[str] = []
    in_code = False
    code_lang = "plain text"
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph).strip()
            if text:
                blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text(text)}})
            paragraph.clear()

    for line in lines:
        if line.startswith("```"):
            if in_code:
                blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": rich_text("\n".join(code_lines)),
                            "language": code_lang,
                        },
                    }
                )
                in_code = False
                code_lines = []
                code_lang = "plain text"
            else:
                flush_paragraph()
                in_code = True
                code_lang = notion_code_language(line[3:])
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            continue

        image_match = re.match(r"!\[(.*?)\]\(([^)]+)\)", line.strip())
        if image_match:
            flush_paragraph()
            caption = image_match.group(1)
            image_src = image_match.group(2).strip()
            if image_src.startswith(("http://", "https://")):
                blocks.append(image_block_from_external(image_src, caption))
            elif image_mode == "upload":
                if not client or not article:
                    raise RuntimeError("Local image upload requires a Notion client and article context")
                image_path = (Path(article["article_dir"]) / urllib.parse.unquote(image_src)).resolve()
                if not image_path.exists():
                    raise FileNotFoundError(f"Local image not found: {image_path}")
                blocks.append(image_block_from_upload(client.upload_file(image_path), caption))
            elif image_mode == "external":
                image_url = asset_url(site_url, article or {}, image_src)
                if not image_url:
                    raise RuntimeError(f"Cannot convert local image to external URL without site_url: {image_src}")
                blocks.append(image_block_from_external(image_url, caption))
            else:
                blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text(line.strip())}})
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            block_type = f"heading_{level}"
            blocks.append({"object": "block", "type": block_type, block_type: {"rich_text": rich_text(heading_match.group(2))}})
            continue

        bullet_match = re.match(r"^\s*[-*]\s+(.+)$", line)
        if bullet_match:
            flush_paragraph()
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": rich_text(bullet_match.group(1))},
                }
            )
            continue

        numbered_match = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if numbered_match:
            flush_paragraph()
            blocks.append(
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": rich_text(numbered_match.group(1))},
                }
            )
            continue

        quote_match = re.match(r"^>\s*(.+)$", line)
        if quote_match:
            flush_paragraph()
            blocks.append({"object": "block", "type": "quote", "quote": {"rich_text": rich_text(quote_match.group(1))}})
            continue

        paragraph.append(line)

    flush_paragraph()
    if in_code:
        blocks.append({"object": "block", "type": "code", "code": {"rich_text": rich_text("\n".join(code_lines)), "language": code_lang}})
    return blocks


def run() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    config = load_config(repo, args.config)
    site_url = args.site_url or config.get("site_url")
    property_map = {**DEFAULT_PROPERTY_MAP, **config.get("property_map", {})}
    articles = discover_articles(repo, config, args.include_drafts)
    if args.slug:
        wanted = set(args.slug)
        articles = [article for article in articles if article["slug"] in wanted]
    if args.limit:
        articles = articles[: args.limit]

    if args.dry_run:
        print(json.dumps({"repo": str(repo), "count": len(articles), "articles": dry_run_articles(articles, site_url)}, ensure_ascii=False, indent=2))
        return 0

    container_id = args.data_source_id or args.database_id
    if not args.token:
        print("NOTION_TOKEN is required unless --dry-run is used", file=sys.stderr)
        return 2
    if not container_id:
        print("NOTION_DATA_SOURCE_ID or NOTION_DATABASE_ID is required unless --dry-run is used", file=sys.stderr)
        return 2

    client = NotionClient(args.token, args.notion_version, use_data_source=bool(args.data_source_id))
    container = client.get_container(container_id)
    schema = schema_properties(container)
    existing = page_index(client.query_pages(container_id), property_map)

    created = 0
    updated = 0
    skipped = 0
    for article in articles:
        page = matching_page(article, existing)
        properties = notion_properties(article, schema, property_map, site_url)
        if page:
            existing_hash = extract_plain_property(page, property_map["content_hash"])
            if existing_hash == article["content_hash"] and not args.force:
                skipped += 1
                continue
            client.update_page(page["id"], properties)
            updated += 1
        else:
            page = client.create_page(container_id, properties)
            created += 1
        if args.content_mode == "full":
            client.replace_children(
                page["id"],
                markdown_blocks(
                    article["body"],
                    article=article,
                    client=client,
                    image_mode=args.image_mode,
                    site_url=site_url,
                ),
            )

    print(json.dumps({"created": created, "updated": updated, "skipped": skipped}, ensure_ascii=False, indent=2))
    return 0


def dry_run_articles(articles: list[dict[str, Any]], site_url: str | None) -> list[dict[str, Any]]:
    return [
        {
            "title": article["title"],
            "section": article["section"],
            "slug": article["slug"],
            "source_path": article["source_path"],
            "url": article_url(site_url, article),
            "hash": article["content_hash"][:12],
            "draft": bool(article["front_matter"].get("draft", False)),
        }
        for article in articles
    ]


if __name__ == "__main__":
    raise SystemExit(run())
