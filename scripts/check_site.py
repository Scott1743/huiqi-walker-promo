#!/usr/bin/env python3
"""Check local references and release versions before publishing this static site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.meta = {}

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for name in ("src", "href", "poster"):
            if attrs.get(name):
                self.links.append(attrs[name])
        if tag == "meta" and attrs.get("name"):
            self.meta[attrs["name"]] = attrs.get("content")


def main():
    errors = []
    release = json.loads((ROOT / "version.json").read_text())
    version = (ROOT / "VERSION").read_text().strip()
    page = Page()
    html = (ROOT / "index.html").read_text()
    page.feed(html)
    if version != release["site_version"]:
        errors.append("VERSION and version.json disagree")
    for name, value in (("site-version", version), ("game-version", release["game_version"])):
        if page.meta.get(name) != value:
            errors.append(f"index.html {name} does not match version.json")

    references = [(ROOT / "index.html", ref) for ref in page.links]
    for source in list(ROOT.glob("*.css")) + [ROOT / "index.html"]:
        references.extend((source, ref) for ref in re.findall(r"url\(['\"]?([^'\")]+)", source.read_text()))
    for source in ROOT.glob("*.md"):
        references.extend((source, ref) for ref in re.findall(r"\]\(([^)]+)\)", source.read_text()))

    for source, ref in references:
        link = urlsplit(ref)
        if link.scheme or link.netloc:
            continue
        if not link.path:
            if source.name == "index.html" and link.fragment and link.fragment not in page.ids:
                errors.append(f"Missing page anchor: {ref}")
            continue
        if link.path.startswith("/"):
            errors.append(f"Project Pages requires relative resource paths: {ref}")
            continue
        destination = (source.parent / unquote(link.path)).resolve()
        if not destination.is_relative_to(ROOT) or not destination.exists():
            errors.append(f"Missing local reference in {source.name}: {ref}")

    files = [path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts]
    for path in files:
        if path.stat().st_size >= 100 * 1024 * 1024:
            errors.append(f"GitHub file size limit: {path.relative_to(ROOT)}")
    if errors:
        raise SystemExit("\n".join(errors))
    total = sum(path.stat().st_size for path in files)
    print(f"OK: site v{version}, game {release['game_version']}; {len(references)} references; {len(files)} files, {total / 1024 / 1024:.1f} MiB")


if __name__ == "__main__":
    main()
