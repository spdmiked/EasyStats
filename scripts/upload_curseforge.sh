#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${CF_API_KEY:-}" || -z "${CF_PROJECT_ID:-}" || -z "${CF_GAME_VERSION_ID:-}" ]]; then
  echo "CurseForge upload skipped: CF_API_KEY, CF_PROJECT_ID, or CF_GAME_VERSION_ID is unset."
  exit 0
fi
root="$(cd "$(dirname "$0")/.." && pwd)"
zip_file="$(find "$root/dist" -maxdepth 1 -name 'EasyStats-*.zip' -print -quit)"
[[ -n "$zip_file" ]] || { echo "EasyStats ZIP not found" >&2; exit 1; }
metadata="$(mktemp)"
trap 'rm -f "$metadata"' EXIT
jq -n --arg version "$CF_GAME_VERSION_ID" --arg changelog "$(cat "$root/CHANGELOG.md")" \
  '{changelog: $changelog, changelogType: "markdown", displayName: env.GITHUB_REF_NAME, gameVersions: [($version | tonumber)], releaseType: "release"}' > "$metadata"
curl --fail-with-body --silent --show-error \
  -H "X-Api-Token: $CF_API_KEY" \
  -F "metadata=@$metadata;type=application/json" \
  -F "file=@$zip_file;type=application/zip" \
  "https://wow.curseforge.com/api/projects/$CF_PROJECT_ID/upload-file"

