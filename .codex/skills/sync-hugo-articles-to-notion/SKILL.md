---
name: sync-hugo-articles-to-notion
description: Sync Hugo Markdown articles into a Notion articles database or data source. Use when Codex needs to publish, mirror, upsert, or refresh posts from this Hugo blog's content/ tree into Notion, including parsing YAML front matter, mapping article metadata to Notion properties, and optionally replacing Notion page body blocks from Markdown content.
---

# Sync Hugo Articles To Notion

## Overview

Use this skill to mirror Hugo articles from this repository into a Notion articles database/data source. Prefer the bundled script for repeatable syncs; only hand-call the Notion API for one-off debugging.

Before syncing, read the repository `context/` files and `MEMORY.md` so article selection, voice, and project conventions match the blog.

## Quick Start

Run the script from the repository root:

```bash
python3 .codex/skills/sync-hugo-articles-to-notion/scripts/sync_hugo_to_notion.py . --dry-run
```

Then sync with credentials:

```bash
NOTION_TOKEN="secret_..." \
NOTION_DATA_SOURCE_ID="..." \
python3 .codex/skills/sync-hugo-articles-to-notion/scripts/sync_hugo_to_notion.py . --content-mode full --image-mode upload
```

Use `NOTION_DATABASE_ID` only for legacy Notion API versions. Prefer `NOTION_DATA_SOURCE_ID` for current Notion APIs.

## Workflow

1. Confirm scope: default to published Markdown articles under `content/`, excluding `_index.md` and drafts.
2. Inspect the Notion schema: read `references/notion-article-schema.md` when creating or adjusting properties.
3. Dry-run first: run the script with `--dry-run` and check selected files, slugs, hashes, and property payloads.
4. Sync metadata: use `--content-mode none` when only the article index/database needs updating.
5. Sync body: use `--content-mode full` to replace Notion page blocks with converted Markdown blocks.
6. Verify a sample page in Notion after the first real sync, especially title, tags, source path, URL, and uploaded local images.

## Script Behavior

The script:

- Parses Hugo YAML front matter and Markdown body.
- Derives `section`, `slug`, `source_path`, and canonical URL from the content path.
- Maps common front matter fields to Notion properties when those properties exist.
- Upserts pages by `Source Path`, then `Slug`, then title.
- Stores `Content Hash` so unchanged articles can be skipped.
- Supports dry-run mode without credentials.
- Converts common Markdown blocks for full-body sync: headings, paragraphs, quotes, bullets, numbered items, code fences, and images.
- Uploads local article images through the Notion File Upload API when `--image-mode upload` is used with a Notion token.

Local relative images must be uploaded into Notion as Notion-hosted files when the available tool/API supports file upload. Do not silently rewrite local article images to public site URLs. If only the Notion connector is available and it does not expose file upload, sync text and metadata, then explicitly report that image upload needs a Notion API token or a browser/UI upload step.

## Configuration

The script works without a config file when the Notion data source uses the recommended schema. Add `.codex/notion-article-sync.json` only when property names differ:

```json
{
  "site_url": "https://example.com",
  "content_dirs": ["content/ai", "content/posts", "content/springweek"],
  "property_map": {
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
    "content_hash": "Content Hash"
  }
}
```

## Safety Notes

- Never print `NOTION_TOKEN`.
- Always run `--dry-run` before the first real sync or after changing schema mappings.
- Do not sync drafts unless the user explicitly asks for drafts or passes `--include-drafts`.
- Treat `public/` and `resources/` as generated output; sync authored Markdown from `content/`.
- Do not replace local image references with public URLs unless the user explicitly asks for link-based images.
- For body sync, the script replaces page children when `--content-mode full`; avoid running it on hand-edited Notion pages unless that overwrite is intended.
