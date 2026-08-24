#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
version="$(sed -n 's/^## Version: //p' "$root/addon/EasyStats/EasyStats.toc")"
mkdir -p "$root/dist"
staging="$(mktemp -d)"
trap 'rm -rf "$staging"' EXIT
cp -R "$root/addon/EasyStats" "$staging/EasyStats"
find "$staging/EasyStats" -type f \( -name '*.tmp' -o -name '*.bak' \) -delete
(cd "$staging" && zip -qr "$root/dist/EasyStats-$version.zip" EasyStats)
echo "$root/dist/EasyStats-$version.zip"

