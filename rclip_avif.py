#!/usr/bin/env python3
"""
rclip-avif.py — search with rclip, then convert the top match to AVIF.

Two-stage by design:
  1. Runs rclip, shows results, extracts the top match's path.
  2. Prompts you for a custom output name. Ctrl+C here to bail out
     before any conversion happens.

Usage:
    rclip-avif.py "<web url or image path>"

Output path is always:
  /home/cluelessyanni/Documents/my-awesome-site/assets/wp-content/uploads/<year>/<month>/<custom_name>.avif

where <year>/<month> are pulled out of the matched file's own path
(e.g. .../uploads/2024/02/17_original.jpgresize600.jpg -> 2024/02).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(
    "/home/cluelessyanni/Documents/my-awesome-site/assets/wp-content/uploads"
)


def run_rclip(query: str) -> str:
    """Run `rclip <query>` and return its stdout (the results table)."""
    result = subprocess.run(["rclip", query], capture_output=True, text=True)

    # rclip's progress bar ("checking images...", the tqdm % bar) is noisy
    # but harmless — just echo it through so you see the same thing you
    # normally would.
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"rclip exited with code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    return result.stdout


def get_top_result(rclip_output: str) -> str:
    """Pull the first /home/... path out of rclip's stdout."""
    print(rclip_output)

    match = re.search(r'/home/\S+', rclip_output)
    if not match:
        print("Error: could not find a result path in rclip output.", file=sys.stderr)
        sys.exit(1)

    # Trailing char will be a stray closing quote from the table formatting.
    return match.group(0).rstrip('"')


def extract_year_month(path: str) -> tuple[str, str]:
    """Pull year/month out of a .../uploads/<year>/<month>/... path."""
    match = re.search(r'uploads/(\d{4})/(\d{2})/', path)
    if not match:
        print(f"Error: couldn't find uploads/<year>/<month>/ in:\n  {path}", file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2)


def main():
    parser = argparse.ArgumentParser(description="rclip search -> avifenc convert workflow")
    parser.add_argument("query", help="Web URL or image path to feed to rclip")
    args = parser.parse_args()

    print(f"Searching with rclip: {args.query}\n")
    output = run_rclip(args.query)

    top_path = get_top_result(output)
    print(f"Top result:\n  {top_path}\n")

    if not Path(top_path).exists():
        print(f"⚠️  Warning: file not found on disk at that path.", file=sys.stderr)

    year, month = extract_year_month(top_path)

    # --- Stage 2: this is the deliberate checkpoint. Ctrl+C here = abort. ---
    try:
        custom_name = input("Custom output name (no extension), or Ctrl+C to abort: ").strip()
    except KeyboardInterrupt:
        print("\nAborted — nothing converted.")
        sys.exit(0)

    if not custom_name:
        print("Error: name cannot be empty.", file=sys.stderr)
        sys.exit(1)

    out_dir = BASE_DIR / year / month
    out_path = out_dir / f"{custom_name}.avif"
    out_dir.mkdir(parents=True, exist_ok=True)

    if out_path.exists():
        try:
            confirm = input(f"⚠️  {out_path} already exists. Overwrite? [y/N] ").strip().lower()
        except KeyboardInterrupt:
            print("\nAborted — nothing converted.")
            sys.exit(0)
        if confirm != "y":
            print("Aborted — nothing converted.")
            sys.exit(0)

    print(f"\nConverting:\n  {top_path}\n  -> {out_path}\n")

    result = subprocess.run(["avifenc", top_path, str(out_path)])
    if result.returncode != 0:
        print("avifenc failed.", file=sys.stderr)
        sys.exit(result.returncode)

    print(f"\n✅ Done: {out_path}")


if __name__ == "__main__":
    main()