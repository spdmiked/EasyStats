#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
addon="$root/addon/EasyStats"
test -f "$addon/EasyStats.toc"
test -f "$addon/GeneratedData.lua"
while IFS= read -r file; do
  [[ -z "$file" || "$file" == '##'* ]] && continue
  test -f "$addon/$file" || { echo "Missing TOC file: $file" >&2; exit 1; }
done < "$addon/EasyStats.toc"
if grep -RIE '(BLIZZARD_CLIENT_SECRET=[A-Za-z0-9]|RAIDERIO_API_KEY=[A-Za-z0-9]|Authorization:[[:space:]]*Bearer[[:space:]]+[A-Za-z0-9])' "$root/addon" "$root/pipeline/src"; then
  echo "Possible committed secret" >&2; exit 1
fi
if command -v luac >/dev/null; then
  find "$addon" -name '*.lua' -print0 | xargs -0 -n1 luac -p
fi
