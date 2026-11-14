"""Rebuild payloads.json (PS5 Payload Manager format) from the latest GitHub releases listed in sources.json.

Standard library only. Uses GITHUB_TOKEN if set. If a source fails, its previous entry is kept.
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "sources.json")
OUTPUT = os.path.join(ROOT, "payloads.json")
CATALOG_NAME = "Ture919 PS5 payloads"


def api(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ps5-payload-catalog"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
        return json.load(r)


def sha256_of(url):
    h = hashlib.sha256()
    req = urllib.request.Request(url, headers={"User-Agent": "ps5-payload-catalog"})
    with urllib.request.urlopen(req, timeout=300) as r:
        for chunk in iter(lambda: r.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build_entry(src):
    releases = api("https://api.github.com/repos/%s/releases?per_page=30" % src["repo"])
    pattern = re.compile(src["asset"])
    for rel in releases:
        if rel.get("draft") or (rel.get("prerelease") and not src.get("prerelease")):
            continue
        assets = [a for a in rel.get("assets", []) if pattern.search(a["name"])]
        if not assets:
            continue
        asset = assets[0]
        digest = asset.get("digest") or ""
        checksum = digest.split(":", 1)[1] if digest.startswith("sha256:") else sha256_of(asset["browser_download_url"])
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise ValueError("bad checksum for %s" % src["id"])
        return {
            "id": src["id"],
            "name": src["name"],
            "filename": asset["name"],
            "url": asset["browser_download_url"],
            "description": src.get("description", ""),
            "version": rel["tag_name"],
            "last_update": (rel.get("published_at") or rel.get("created_at") or "")[:10],
            "category": src.get("category", "Uncategorized"),
            "checksum": checksum,
            "author": src.get("author", ""),
            "source": rel["html_url"],
        }
    raise ValueError("no release with a matching asset for %s" % src["id"])


def main():
    with open(SOURCES, encoding="utf-8") as f:
        sources = json.load(f)
    previous = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT, encoding="utf-8") as f:
            previous = {p["id"]: p for p in json.load(f).get("payloads", [])}
    payloads, errors = [], 0
    for src in sources:
        try:
            payloads.append(build_entry(src))
        except Exception as e:  # keep the last good entry
            errors += 1
            print("ERROR %s: %s" % (src["id"], e), file=sys.stderr)
            if src["id"] in previous:
                payloads.append(previous[src["id"]])
    catalog = {"name": CATALOG_NAME, "payloads": payloads}
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        f.write("\n")
    for p in payloads:
        print("%-22s %-12s %s" % (p["id"], p["version"], p["last_update"]))
    return 1 if errors and not payloads else 0


if __name__ == "__main__":
    sys.exit(main())
