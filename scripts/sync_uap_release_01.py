#!/usr/bin/env python3
"""Sync PURSUE Release 01 UAP files into the Hugo static tree.

The committed manifest is the source of truth for the site. Use
--refresh-manifest when the upstream Release 01 archive index changes.
"""

from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
from typing import Any
from urllib.parse import quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "uap_release_01.json"
DOWNLOAD_ROOT = ROOT / ".cache" / "uap-release-01-files"
REPORT_PATH = ROOT / "static" / "uap" / "release-01" / "sync-report.json"
ENV_PATH = ROOT / ".env.local"
ARCHIVE_URL = "https://warufo.com/archive"
DETAIL_URL_TEMPLATE = "https://warufo.com/document/{number}"
OFFICIAL_INDEX_URL = "https://www.war.gov/UFO/"
PURSUE_INDEX_MANIFEST_URL = "https://raw.githubusercontent.com/BPSAI/pursue-index/main/web/src/data/manifest.json"
PURSUE_INDEX_PDF_URL_TEMPLATE = "https://pursueindex.com/pdf/{card_id}.pdf"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


AGENCY_ZH = {
    "Department of War": "美国战争部",
    "FBI": "联邦调查局",
    "NASA": "美国国家航空航天局",
    "Department of State": "美国国务院",
}

SECTION_DIR = ROOT / "content" / "uap" / "release-01"

KIND_ZH = {
    "pdf": "PDF 文档",
    "image": "图片",
    "video": "视频",
}


def load_local_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def r2_public_base_url() -> str:
    load_local_env()
    base_url = os.environ.get("R2_PUBLIC_BASE_URL", "").strip().rstrip("/")
    if ".r2.cloudflarestorage.com" in base_url:
        return ""
    return base_url


class ArchiveTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict[str, Any]] = []
        self._row: dict[str, Any] | None = None
        self._cells: list[str] = []
        self._cell_links: list[list[str]] = []
        self._in_cell = False
        self._cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "tr" and "data-agency" in attr:
            self._row = {"agency": attr.get("data-agency", "")}
            self._cells = []
            self._cell_links = []
        elif self._row is not None and tag == "td":
            self._in_cell = True
            self._cell_parts = []
            self._cell_links.append([])
        elif self._in_cell and tag == "a":
            href = attr.get("href")
            if href:
                self._cell_links[-1].append(html.unescape(href))

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._in_cell:
            text = " ".join("".join(self._cell_parts).split())
            self._cells.append(html.unescape(text))
            self._in_cell = False
            self._cell_parts = []
        elif tag == "tr" and self._row is not None:
            row = self._row
            cells = self._cells
            if len(cells) >= 7:
                source_url = ""
                for href in self._cell_links[-1]:
                    if href.startswith("http"):
                        source_url = href
                        break
                if source_url:
                    row.update(
                        {
                            "number": int(cells[0]),
                            "agency": row["agency"],
                            "agency_label": cells[1],
                            "title": cells[2],
                            "description": cells[3],
                            "date": "" if cells[4] == "N/A" else cells[4],
                            "location": "" if cells[5] == "N/A" else cells[5],
                            "source_url": source_url,
                        }
                    )
                    self.records.append(row)
            self._row = None


def request_url(url: str, timeout: int = 120) -> bytes:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.war.gov/UFO/",
        },
    )
    with urlopen(req, timeout=timeout) as response:
        return response.read()


def classify_url(url: str) -> str:
    path = urlparse(url).path.lower()
    if "dvidshub.net/video/" in url:
        return "video"
    if path.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return "image"
    return "pdf"


def extension_for(record: dict[str, Any]) -> str:
    kind = record["kind"]
    if kind == "video":
        return ".mp4"
    path = urlparse(record["source_url"]).path
    suffix = Path(unquote(path)).suffix.lower()
    if suffix in {".pdf", ".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    return ".pdf" if kind == "pdf" else ".bin"


def slugify(value: str, max_len: int = 96) -> str:
    value = unquote(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return (value[:max_len].strip("-") or "uap-file")


def local_relpath(record: dict[str, Any]) -> str:
    folder = {"pdf": "pdf", "image": "images", "video": "videos"}[record["kind"]]
    slug = slugify(record["title"])
    return f"uap/release-01/files/{folder}/{record['number']:03d}-{slug}{extension_for(record)}"


def cache_path_for_relpath(relpath: str) -> Path:
    prefix = "uap/release-01/files/"
    if relpath.startswith(prefix):
        return DOWNLOAD_ROOT / relpath[len(prefix) :]
    return DOWNLOAD_ROOT / relpath


def local_file_exists(relpath: str) -> bool:
    return cache_path_for_relpath(relpath).exists() or (ROOT / "static" / relpath).exists()


def dvids_page_url(embed_url: str) -> str:
    match = re.search(r"/video/embed/(\d+)", embed_url)
    if match:
        return f"https://www.dvidshub.net/video/{match.group(1)}"
    return embed_url


def video_relpath(record: dict[str, Any]) -> str:
    if record.get("kind") == "video":
        return record["local_path"]
    slug = slugify(record.get("detail_title") or record["title"])
    return f"uap/release-01/files/videos/{int(record['number']):03d}-{slug}.mp4"


def refresh_manifest() -> list[dict[str, Any]]:
    body = request_url(ARCHIVE_URL).decode("utf-8", errors="replace")
    parser = ArchiveTableParser()
    parser.feed(body)
    if not parser.records:
        raise RuntimeError("No Release 01 records found in archive index")

    records: list[dict[str, Any]] = []
    for item in sorted(parser.records, key=lambda x: x["number"]):
        kind = classify_url(item["source_url"])
        record = {
            "number": item["number"],
            "title": item["title"],
            "agency": item["agency"],
            "agency_zh": AGENCY_ZH.get(item["agency"], item["agency"]),
            "kind": kind,
            "kind_zh": KIND_ZH[kind],
            "date": item["date"],
            "location": item["location"],
            "description": item["description"],
            "source_url": item["source_url"],
        }
        record["local_path"] = local_relpath(record)
        records.append(record)
    return records


def write_manifest(records: list[dict[str, Any]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_manifest() -> list[dict[str, Any]]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def extract_first(pattern: str, body: str, default: str = "", flags: int = re.S) -> str:
    match = re.search(pattern, body, flags)
    return strip_tags(match.group(1)) if match else default


def extract_attr(pattern: str, body: str, default: str = "", flags: int = re.S) -> str:
    match = re.search(pattern, body, flags)
    return html.unescape(match.group(1)) if match else default


def fetch_detail(record: dict[str, Any]) -> dict[str, Any]:
    detail_url = DETAIL_URL_TEMPLATE.format(number=int(record["number"]))
    body = request_url(detail_url).decode("utf-8", errors="replace")
    metadata: dict[str, str] = {}
    for label, value in re.findall(r"<span>(Released:|Incident:|Location:)\s*([^<]+)</span>", body):
        metadata[label.rstrip(":").lower()] = strip_tags(value)

    download_links = [
        html.unescape(link)
        for link in re.findall(r'<a\s+href="([^"]+)"[^>]*class="btn[^"]*"', body)
        if link.startswith("http")
    ]
    embed_url = extract_attr(r'<iframe\s+src="([^"]+)"', body)
    thumbnail_url = extract_attr(r'<img\s+src="([^"]+)"[^>]+alt=', body)
    title = extract_first(r'<h1[^>]*class="section-title"[^>]*>(.*?)</h1>', body, record["title"])
    file_id = extract_first(
        r"<p[^>]*JetBrains Mono[^>]*>(.*?)</p>",
        body,
        record["title"],
    )
    description = extract_first(r'<div class="exec-brief"[^>]*><p>(.*?)</p></div>', body, record.get("description", ""))

    return {
        "detail_source_url": detail_url,
        "official_index_url": OFFICIAL_INDEX_URL,
        "detail_title": title,
        "file_id": file_id,
        "released": metadata.get("released", "5/8/26"),
        "incident_date": metadata.get("incident", record.get("date", "")),
        "location": metadata.get("location", record.get("location", "")),
        "detail_description": description,
        "thumbnail_url": thumbnail_url,
        "embed_url": embed_url,
        "video_source_url": dvids_page_url(embed_url) if embed_url else "",
        "video_local_path": video_relpath({**record, "detail_title": title}) if embed_url else "",
        "detail_links": download_links,
    }


def translate_text(text: str, sleep_seconds: float = 0.08, attempts: int = 3) -> str:
    text = " ".join(text.split())
    if not text:
        return ""
    params = urlencode({"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": text})
    url = "https://translate.googleapis.com/translate_a/single?" + params
    req = Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(req, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
            time.sleep(sleep_seconds)
            return "".join(part[0] for part in data[0] if part and part[0]).strip()
        except Exception as exc:
            last_error = exc
            time.sleep(attempt * 0.8)
    print(f"Translation failed after {attempts} attempts: {last_error}", file=sys.stderr)
    return text


def enrich_details(records: list[dict[str, Any]], force_translate: bool = False, limit: int | None = None) -> list[dict[str, Any]]:
    selected = records if limit is None else records[:limit]
    by_number = {int(record["number"]): record for record in records}
    for record in selected:
        number = int(record["number"])
        print(f"Fetching detail {number:03d}: {record['title']}", flush=True)
        try:
            detail = fetch_detail(record)
            record.update(detail)
            record["detail_fetch_error"] = ""
        except Exception as exc:
            record["detail_fetch_error"] = str(exc)
            record.setdefault("detail_title", record["title"])
            record.setdefault("detail_description", record.get("description", ""))
        record["page_path"] = f"/uap/release-01/{number:03d}-{slugify(record.get('detail_title') or record['title'])}/"
        if force_translate or not record.get("title_zh"):
            record["title_zh"] = translate_text(record.get("detail_title") or record["title"])
        if force_translate or not record.get("description_zh"):
            record["description_zh"] = translate_text(record.get("detail_description") or record.get("description", ""))
        by_number[number] = record
    return [by_number[int(record["number"])] for record in records]


def yaml_quote(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def front_matter(record: dict[str, Any]) -> str:
    fields = {
        "title": record.get("title_zh") or record.get("detail_title") or record["title"],
        "date": "2026-05-08",
        "draft": "false",
        "description": record.get("description_zh", ""),
        "original_title": record.get("detail_title") or record["title"],
        "record_number": int(record["number"]),
        "agency": record.get("agency", ""),
        "agency_zh": record.get("agency_zh", ""),
        "file_kind": record.get("kind", ""),
        "kind_zh": record.get("kind_zh", ""),
        "released": record.get("released", ""),
        "incident_date": record.get("incident_date", ""),
        "location": record.get("location", ""),
        "source_url": record.get("source_url", ""),
        "official_index_url": record.get("official_index_url", OFFICIAL_INDEX_URL),
        "detail_source_url": record.get("detail_source_url", ""),
        "embed_url": record.get("embed_url", ""),
        "series": '["UAP Release 01"]',
        "categories": '["UAP"]',
        "tags": '["UAP", "PURSUE", "Release 01"]',
    }
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, int) or value == "false" or (isinstance(value, str) and value.startswith("[")):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {yaml_quote(value)}")
    lines.append("---")
    return "\n".join(lines)


def markdown_link(label: str, url: str) -> str:
    if not url:
        return ""
    safe_label = label.replace("[", "\\[").replace("]", "\\]")
    return f"[{safe_label}]({url})"


def page_markdown(record: dict[str, Any]) -> str:
    detail_title = record.get("detail_title") or record["title"]
    title_zh = record.get("title_zh") or detail_title
    description_zh = record.get("description_zh") or "暂无中文摘要。"
    local_path = record.get("local_path", "")
    remote_base_url = r2_public_base_url()
    local_url = ""
    if local_path and local_file_exists(local_path):
        local_url = f"{remote_base_url}/{local_path}" if remote_base_url else "/" + local_path
    video_local_path = record.get("video_local_path", "")
    video_local_url = ""
    if video_local_path and local_file_exists(video_local_path):
        video_local_url = f"{remote_base_url}/{video_local_path}" if remote_base_url else "/" + video_local_path

    parts = [front_matter(record), ""]
    parts.extend(
        [
            f"这是 PURSUE Release 01 第 {int(record['number']):03d} 条记录的中文详情页。",
            "",
            "## 基本信息",
            "",
            f"- 原始标题：{detail_title}",
            f"- 中文标题：{title_zh}",
            f"- 发布机构：{record.get('agency_zh', record.get('agency', ''))}",
            f"- 文件类型：{record.get('kind_zh', record.get('kind', ''))}",
            f"- 公开日期：{record.get('released', '2026-05-08')}",
        ]
    )
    if record.get("incident_date"):
        parts.append(f"- 事件日期：{record['incident_date']}")
    if record.get("location"):
        parts.append(f"- 地点：{record['location']}")

    parts.extend(["", "## 中文摘要", "", description_zh, "", "## 文件与来源", ""])
    parts.append(f"- 原始文件：{markdown_link(record.get('source_url', ''), record.get('source_url', ''))}")
    if local_url:
        parts.append(f"- 本地同步文件：{markdown_link(local_url, local_url)}")
    else:
        parts.append("- 本地同步文件：当前未下载到本地，页面先保留官方来源链接。")
    if record.get("embed_url"):
        if video_local_url:
            parts.append(f"- 本地同步媒体：{markdown_link(video_local_url, video_local_url)}")
        else:
            parts.append("- 本地同步媒体：当前未下载到本地，页面先保留 DVIDS 嵌入。")
    parts.append(f"- 官方索引页：{markdown_link(OFFICIAL_INDEX_URL, OFFICIAL_INDEX_URL)}")
    if record.get("detail_source_url"):
        parts.append(f"- 详情数据源：{markdown_link(record['detail_source_url'], record['detail_source_url'])}")

    if record.get("embed_url"):
        parts.extend(["", "## 媒体", ""])
        if video_local_url:
            parts.extend(
                [
                    f'<video controls preload="metadata" src="{video_local_url}" style="width:100%;border-radius:8px;border:1px solid var(--linear-border);background:#000"></video>',
                    "",
                    f"备用来源：{markdown_link('DVIDS 嵌入页', record['embed_url'])}",
                ]
            )
        else:
            parts.append(f'<iframe src="{record["embed_url"]}" width="100%" height="480" frameborder="0" allowfullscreen loading="lazy"></iframe>')
    elif record.get("kind") == "image":
        image_url = local_url or record.get("source_url", "")
        parts.extend(["", "## 图片", "", f"![{detail_title}]({image_url})"])
    elif record.get("thumbnail_url"):
        parts.extend(["", "## 预览图", "", f'![{detail_title}]({record["thumbnail_url"]})'])

    return "\n".join(parts).strip() + "\n"


def write_detail_pages(records: list[dict[str, Any]]) -> None:
    SECTION_DIR.mkdir(parents=True, exist_ok=True)
    index_path = SECTION_DIR / "_index.md"
    if not index_path.exists():
        index_path.write_text(
            "---\ntitle: \"Release 01\"\ndescription: \"PURSUE Release 01 的逐条中文详情。\"\n---\n",
            encoding="utf-8",
        )
    for record in records:
        if not record.get("page_path"):
            record["page_path"] = f"/uap/release-01/{int(record['number']):03d}-{slugify(record.get('detail_title') or record['title'])}/"
        slug = record["page_path"].strip("/").split("/")[-1]
        page_dir = SECTION_DIR / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.md").write_text(page_markdown(record), encoding="utf-8")


def safe_url(url: str) -> str:
    parsed = urlparse(url)
    path = quote(unquote(parsed.path), safe="/-._~[]',")
    return parsed._replace(path=path).geturl()


def source_filename(url: str) -> str:
    return Path(unquote(urlparse(url).path)).name.lower()


def load_pursue_pdf_mirrors() -> dict[str, str]:
    """Map war.gov PDF URLs and filenames to pursueindex.com mirrored PDFs."""
    try:
        data = json.loads(request_url(PURSUE_INDEX_MANIFEST_URL, timeout=45).decode("utf-8"))
    except Exception as exc:
        print(f"Could not load pursueindex.com PDF mirror manifest: {exc}", file=sys.stderr)
        return {}

    mirrors: dict[str, str] = {}
    for card in data.get("cards", []):
        card_id = card.get("card_id")
        asset_url = card.get("asset_url") or ""
        if not card_id or not asset_url or not asset_url.lower().endswith(".pdf"):
            continue
        mirror_url = PURSUE_INDEX_PDF_URL_TEMPLATE.format(card_id=card_id)
        mirrors[asset_url.lower()] = mirror_url
        mirrors[source_filename(asset_url)] = mirror_url
    return mirrors


def resolve_dvids_mp4(url: str) -> str:
    body = request_url(url).decode("utf-8", errors="replace")
    match = re.search(r'<source\s+src="([^"]+\.mp4)"', body)
    if not match:
        match = re.search(r'https://[^"\s]+\.mp4', body)
    if not match:
        raise RuntimeError("Could not resolve DVIDS MP4 source")
    return html.unescape(match.group(1))


def download_bytes(url: str, timeout: int) -> tuple[bytes, str]:
    try:
        from curl_cffi import requests as curl_requests  # type: ignore

        response = curl_requests.get(
            url,
            impersonate="chrome124",
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Referer": "https://www.war.gov/UFO/"},
        )
        return response.content, str(response.status_code)
    except Exception:
        req = Request(url, headers={"User-Agent": USER_AGENT, "Referer": "https://www.war.gov/UFO/"})
        with urlopen(req, timeout=timeout) as response:
            return response.read(), str(response.status)


def looks_valid(record: dict[str, Any], payload: bytes) -> bool:
    if record["kind"] == "pdf":
        return payload.startswith(b"%PDF")
    if record["kind"] == "image":
        return payload.startswith((b"\x89PNG", b"\xff\xd8\xff", b"RIFF"))
    if record["kind"] == "video":
        return b"ftyp" in payload[:64]
    return bool(payload)


def sync_files(records: list[dict[str, Any]], include: set[str], limit: int | None, timeout: int) -> dict[str, Any]:
    results: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "downloaded": [],
        "skipped": [],
        "failed": [],
    }
    selected = [
        r
        for r in records
        if r["kind"] in include or ("video" in include and r.get("embed_url"))
    ]
    if limit is not None:
        selected = selected[:limit]

    pdf_mirrors = load_pursue_pdf_mirrors() if "pdf" in include else {}

    for record in selected:
        download_kind = "video" if "video" in include and record.get("embed_url") else record["kind"]
        destination_rel = record.get("video_local_path") if download_kind == "video" and record.get("embed_url") else record["local_path"]
        destination = cache_path_for_relpath(destination_rel)
        if destination.exists() and destination.stat().st_size > 0:
            results["skipped"].append({"number": record["number"], "path": destination_rel})
            continue

        source = record.get("video_source_url") if download_kind == "video" and record.get("embed_url") else record["source_url"]
        sources = [source]
        if download_kind == "pdf":
            mirror = pdf_mirrors.get(source.lower()) or pdf_mirrors.get(source_filename(source))
            if mirror:
                sources = [source, mirror]

        attempted: list[str] = []
        try:
            last_error: Exception | None = None
            payload = b""
            status = ""
            resolved_source = ""
            for candidate in sources:
                attempted.append(candidate)
                try:
                    resolved_source = candidate
                    if download_kind == "video" and "dvidshub.net/video/" in candidate:
                        resolved_source = resolve_dvids_mp4(candidate)
                    payload, status = download_bytes(safe_url(resolved_source), timeout)
                    validation_record = {**record, "kind": download_kind}
                    if not looks_valid(validation_record, payload):
                        raise RuntimeError(f"invalid {download_kind} payload, status={status}, bytes={len(payload)}")
                    break
                except Exception as exc:
                    last_error = exc
            else:
                raise RuntimeError(str(last_error) if last_error else "no download source available")

            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(delete=False, dir=destination.parent) as tmp:
                tmp.write(payload)
                tmp_path = Path(tmp.name)
            shutil.move(str(tmp_path), destination)
            results["downloaded"].append(
                {
                    "number": record["number"],
                    "path": destination_rel,
                    "source_url": resolved_source,
                    "bytes": destination.stat().st_size,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        except Exception as exc:
            results["failed"].append(
                {
                    "number": record["number"],
                    "title": record["title"],
                    "kind": download_kind,
                    "source_url": source,
                    "attempted_urls": attempted,
                    "error": str(exc),
                }
            )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-manifest", action="store_true", help="scrape the Release 01 archive index and rewrite data/uap_release_01.json")
    parser.add_argument("--refresh-details", action="store_true", help="scrape per-record detail pages and translate titles/summaries into Chinese")
    parser.add_argument("--force-translate", action="store_true", help="translate titles/summaries even when Chinese fields already exist")
    parser.add_argument("--write-pages", action="store_true", help="write one Hugo detail page per Release 01 record")
    parser.add_argument("--manifest-only", action="store_true", help="refresh or validate manifest without downloading files")
    parser.add_argument("--include", default="pdf,image,video", help="comma-separated kinds to download: pdf,image,video")
    parser.add_argument("--limit", type=int, help="download only the first N selected records")
    parser.add_argument("--timeout", type=int, default=180, help="per-request timeout in seconds")
    parser.add_argument("--allow-failures", action="store_true", help="exit 0 even when some files could not be downloaded")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.refresh_manifest:
        records = refresh_manifest()
        write_manifest(records)
    else:
        records = load_manifest()

    counts: dict[str, int] = {}
    for record in records:
        counts[record["kind"]] = counts.get(record["kind"], 0) + 1
    print(f"Release 01 manifest: {len(records)} records ({counts})")

    if args.refresh_details:
        records = enrich_details(records, force_translate=args.force_translate, limit=args.limit)
        write_manifest(records)

    if args.write_pages:
        write_detail_pages(records)
        print(f"Wrote {len(records)} detail pages under {SECTION_DIR}")

    if args.manifest_only:
        return 0

    include = {item.strip() for item in args.include.split(",") if item.strip()}
    results = sync_files(records, include, args.limit, args.timeout)
    print(
        "Sync complete: "
        f"{len(results['downloaded'])} downloaded, "
        f"{len(results['skipped'])} skipped, "
        f"{len(results['failed'])} failed"
    )
    if results["failed"] and not args.allow_failures:
        print(f"See {REPORT_PATH}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
