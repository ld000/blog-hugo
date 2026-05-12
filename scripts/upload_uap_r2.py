#!/usr/bin/env python3
"""Upload synced UAP media files to Cloudflare R2.

Reads credentials from .env.local by default. Secrets are never printed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import http.client
import mimetypes
import os
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / ".cache" / "uap-release-01-files"
ENV_PATH = ROOT / ".env.local"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing {name}")
    return value


def sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def signing_key(secret: str, date_stamp: str, region: str, service: str) -> bytes:
    key = sign(("AWS4" + secret).encode("utf-8"), date_stamp)
    key = sign(key, region)
    key = sign(key, service)
    return sign(key, "aws4_request")


def canonical_key(key: str) -> str:
    return "/".join(quote(part, safe="-_.~") for part in key.split("/"))


class R2Client:
    def __init__(self, account_id: str, bucket: str, access_key: str, secret_key: str) -> None:
        self.host = f"{account_id}.r2.cloudflarestorage.com"
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = "auto"
        self.service = "s3"

    def _headers(self, method: str, path: str, payload_hash: str, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        now = dt.datetime.now(dt.UTC)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        headers = {
            "host": self.host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        if extra_headers:
            headers.update({k.lower(): v for k, v in extra_headers.items()})

        signed_headers = ";".join(sorted(headers))
        canonical_headers = "".join(f"{name}:{headers[name].strip()}\n" for name in sorted(headers))
        canonical_request = "\n".join(
            [
                method,
                path,
                "",
                canonical_headers,
                signed_headers,
                payload_hash,
            ]
        )
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                amz_date,
                credential_scope,
                hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )
        signature = hmac.new(
            signing_key(self.secret_key, date_stamp, self.region, self.service),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        headers["authorization"] = (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )
        return headers

    def object_path(self, key: str) -> str:
        return f"/{canonical_key(self.bucket)}/{canonical_key(key)}"

    def head(self, key: str) -> tuple[int, dict[str, str]]:
        path = self.object_path(key)
        payload_hash = hashlib.sha256(b"").hexdigest()
        headers = self._headers("HEAD", path, payload_hash)
        conn = http.client.HTTPSConnection(self.host, timeout=60)
        conn.request("HEAD", path, headers=headers)
        response = conn.getresponse()
        response.read()
        result_headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        return response.status, result_headers

    def put_file(self, key: str, path: Path, content_type: str) -> int:
        payload_hash = sha256_file(path)
        object_path = self.object_path(key)
        headers = self._headers(
            "PUT",
            object_path,
            payload_hash,
            {
                "content-length": str(path.stat().st_size),
                "content-type": content_type,
            },
        )
        conn = http.client.HTTPSConnection(self.host, timeout=600)
        with path.open("rb") as body:
            conn.request("PUT", object_path, body=body, headers=headers)
            response = conn.getresponse()
            response.read()
        conn.close()
        return response.status


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def iter_files(source: Path) -> list[Path]:
    return sorted(
        (path for path in source.rglob("*") if path.is_file()),
        key=lambda path: (path.stat().st_size, path.as_posix()),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", type=Path, default=ENV_PATH)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--prefix", default="uap/release-01/files")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env(args.env)
    client = R2Client(
        account_id=require_env("R2_ACCOUNT_ID"),
        bucket=require_env("R2_BUCKET"),
        access_key=require_env("R2_ACCESS_KEY_ID"),
        secret_key=require_env("R2_SECRET_ACCESS_KEY"),
    )
    public_base_url = require_env("R2_PUBLIC_BASE_URL").rstrip("/")

    source = args.source.resolve()
    if not source.exists():
        legacy_source = ROOT / "static" / "uap" / "release-01" / "files"
        if source == DEFAULT_SOURCE.resolve() and legacy_source.exists():
            source = legacy_source.resolve()
        else:
            raise RuntimeError(f"Source directory does not exist: {source}")
    files = iter_files(source)
    uploaded = 0
    skipped = 0
    failed = 0
    total_bytes = 0

    print(f"Uploading {len(files)} files from {source}", flush=True)
    print(f"Public base URL: {public_base_url}", flush=True)
    for index, path in enumerate(files, start=1):
        relative = path.relative_to(source).as_posix()
        key = f"{args.prefix.strip('/')}/{relative}"
        size = path.stat().st_size
        total_bytes += size

        status, headers = client.head(key)
        remote_size = int(headers.get("content-length", "-1")) if headers.get("content-length", "").isdigit() else -1
        if status == 200 and remote_size == size:
            skipped += 1
            print(f"[{index}/{len(files)}] skip {key}", flush=True)
            continue

        if args.dry_run:
            print(f"[{index}/{len(files)}] would upload {key} ({size} bytes)", flush=True)
            continue

        try:
            print(f"[{index}/{len(files)}] uploading {key} ({size} bytes)", flush=True)
            put_status = client.put_file(key, path, content_type(path))
            if put_status not in {200, 201, 204}:
                raise RuntimeError(f"PUT returned HTTP {put_status}")
            uploaded += 1
            print(f"[{index}/{len(files)}] uploaded {key}", flush=True)
        except Exception as exc:
            failed += 1
            print(f"[{index}/{len(files)}] failed {key}: {exc}", flush=True)

    print(
        "Upload complete: "
        f"{uploaded} uploaded, {skipped} skipped, {failed} failed, "
        f"{total_bytes} bytes scanned",
        flush=True,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
