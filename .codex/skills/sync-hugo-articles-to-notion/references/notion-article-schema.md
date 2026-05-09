# Notion Article Schema

Use this reference when creating or checking the Notion articles database/data source used by `sync-hugo-articles-to-notion`.

## Recommended Properties

| Purpose | Notion property | Type | Source |
| --- | --- | --- | --- |
| Title | `Name` | title | front matter `title` |
| Slug | `Slug` | rich text | derived from path |
| Source path | `Source Path` | rich text | repo-relative Markdown path |
| Section | `Section` | select | first folder under `content/` |
| Publish date | `Date` | date | front matter `date` |
| Tags | `Tags` | multi-select | front matter `tags` |
| Categories | `Categories` | multi-select | front matter `categories` |
| Series | `Series` | multi-select | front matter `series` |
| Description | `Description` | rich text | front matter `description` |
| Draft flag | `Draft` | checkbox | front matter `draft` |
| Canonical URL | `URL` | url | `site_url` + section + slug |
| Last sync time | `Last Synced` | date | sync timestamp |
| Content hash | `Content Hash` | rich text | SHA-256 of article source |

Only `Name` is required. The sync script skips optional properties that are not present in Notion, so the database can start minimal and evolve.

## Current Notion API Notes

Prefer current Notion data sources over legacy databases:

- Create pages under a data source when using modern Notion API versions.
- Query a data source to find existing synced pages.
- Legacy `database_id` mode remains available for older workspaces or pinned API versions.
- Official references: [Create a page](https://developers.notion.com/reference/post-page), [Parent object](https://developers.notion.com/reference/parent-object), and [2025-09-03 upgrade guide](https://developers.notion.com/guides/get-started/upgrade-guide-2025-09-03).
- For local article images, use the Notion File Upload API instead of external image URLs when a Notion API token is available.

Keep API-version-specific details in the script rather than in prompts. If a sync fails with a schema or parent error, check the current Notion docs and adjust `NOTION_VERSION`, `NOTION_DATA_SOURCE_ID`, or the parent payload handling.

## Property Mapping Rules

- `title`: write to the first Notion `title` property, even if it is not named `Name`.
- `tags`, `categories`, `series`: write arrays as multi-select names.
- `date`: write ISO date strings to a Notion date property.
- `draft`: write booleans to a checkbox.
- `url`: write only absolute URLs.
- `content_hash`: compare before updating to skip unchanged articles.

## Common Sync Modes

- Metadata index only: `--content-mode none`
- Full mirror: `--content-mode full`
- Include drafts intentionally: `--include-drafts`
- Sync one article: `--slug 2026-2-langchain-langgraph-langsmith`
- Test property mapping without API calls: `--dry-run`
