#!/usr/bin/env python3
"""
Filter-copy script: copies notes with dg-publish: true from Obsidian vault
to Quartz content/ directory, along with referenced assets.
Cleans stale files that no longer have dg-publish: true.
"""

import os
import re
import shutil
import sys
from pathlib import Path

VAULT = Path.home() / "Obsidian_root"
CONTENT = Path(__file__).parent.parent / "content"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
PUBLISH_RE = re.compile(r"^\s*dg-publish\s*:\s*true\s*$", re.MULTILINE)
ASSET_RE = re.compile(r"!\[\[([^\]]+)\]\]|!\[.*?\]\(([^)]+)\)")


def has_publish_flag(md_path: Path) -> bool:
    try:
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        m = FRONTMATTER_RE.match(text)
        if m and PUBLISH_RE.search(m.group(1)):
            return True
    except Exception:
        pass
    return False


def find_referenced_assets(md_path: Path) -> list[Path]:
    assets = []
    try:
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        for match in ASSET_RE.finditer(text):
            ref = match.group(1) or match.group(2)
            if not ref:
                continue
            # Try relative to note first, then vault root
            candidate = md_path.parent / ref
            if candidate.exists():
                assets.append(candidate.resolve())
                continue
            candidate = VAULT / ref
            if candidate.exists():
                assets.append(candidate.resolve())
    except Exception:
        pass
    return assets


def main():
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv or dry_run

    # Collect published notes
    published: dict[Path, Path] = {}  # vault_path -> content_path
    for md in VAULT.rglob("*.md"):
        if has_publish_flag(md):
            rel = md.relative_to(VAULT)
            dest = CONTENT / rel
            published[md] = dest

    print(f"Found {len(published)} notes with dg-publish: true")

    # Copy notes
    copied = 0
    for src, dst in published.items():
        if dry_run:
            print(f"  [DRY] copy {src.relative_to(VAULT)} -> content/{dst.relative_to(CONTENT)}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
        if verbose:
            print(f"  + {src.relative_to(VAULT)}")

    # Copy referenced assets
    asset_count = 0
    for src in published:
        for asset in find_referenced_assets(src):
            try:
                rel = asset.relative_to(VAULT)
                dst = CONTENT / rel
                if dry_run:
                    print(f"  [DRY] asset {rel}")
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(asset, dst)
                asset_count += 1
                if verbose:
                    print(f"  + asset: {rel}")
            except ValueError:
                pass  # asset outside vault, skip

    # Clean stale .md files from content/ that are no longer published
    removed = 0
    dest_paths = set(published.values())
    for existing in CONTENT.rglob("*.md"):
        if existing.name == ".gitkeep":
            continue
        if existing not in dest_paths:
            if dry_run:
                print(f"  [DRY] remove stale {existing.relative_to(CONTENT)}")
                continue
            existing.unlink()
            removed += 1
            if verbose:
                print(f"  - removed stale: {existing.relative_to(CONTENT)}")

    if not dry_run:
        print(f"Copied {copied} notes, {asset_count} assets. Removed {removed} stale files.")
    else:
        print("Dry run complete — no files modified.")


if __name__ == "__main__":
    main()
