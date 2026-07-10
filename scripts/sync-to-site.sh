#!/usr/bin/env bash
# Copy the built index.html into a checkout of the adamdaniel.ai site repo,
# record provenance, and commit + force-push a sync/preview branch there.
#
# The site vendors the map verbatim at assets/tools/claude-memory-map/index.html
# (see the site repo's AGENTS.md "Tools section"). This script is the single
# write path shared by both workflows:
#   site-sync.yml     BRANCH=tool-sync/claude-memory-map            (main → auto-merge PR)
#   site-preview.yml  BRANCH=tool-preview/claude-memory-map-pr-<n>  (PR mirror, draft)
#
# It relies on CI's drift check: the committed index.html is guaranteed to be
# the deterministic output of `npm run build`, so copying the committed file
# is copying the built artifact.
#
# Inputs (env):
#   SITE_DIR       path to the site checkout (cloned with push credentials)
#   BRANCH         site branch to create/force-push (based on SITE_DIR's HEAD)
#   SOURCE_COMMIT  memory-map commit the copy comes from (must equal this
#                  repo's checked-out HEAD)
#   SOURCE_REF     provenance label: "main" or "pr-<n>"
#   SOURCE_PR      optional source PR number, recorded for preview mirrors
#   COMMIT_MSG     commit message for the site commit
#
# Outputs (appended to $GITHUB_OUTPUT when set, echoed either way):
#   changed=true|false      whether a site commit was pushed
#   previous_commit=<sha>   the source commit the site had before (may be empty)
set -euo pipefail

: "${SITE_DIR:?}" "${BRANCH:?}" "${SOURCE_COMMIT:?}" "${SOURCE_REF:?}" "${COMMIT_MSG:?}"

here=$(cd "$(dirname "$0")/.." && pwd)
asset_dir="$SITE_DIR/assets/tools/claude-memory-map"
data_dir="$SITE_DIR/_data/tool_sources"

out() {
  if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "$1" >>"$GITHUB_OUTPUT"; fi
  echo "$1"
}

if [ "$(git -C "$here" rev-parse HEAD)" != "$SOURCE_COMMIT" ]; then
  echo "::error::checkout HEAD does not match SOURCE_COMMIT=$SOURCE_COMMIT" >&2
  exit 1
fi

# The site opts in by having the vendored directory (it lands in
# adamdaniel.ai#2280). Before that, syncing would create an orphan asset with
# no /tools/ page — skip instead of surprising the site with new files.
if [ ! -d "$asset_dir" ]; then
  echo "::warning::$asset_dir does not exist on the site branch — the site has not vendored this tool (yet); skipping."
  out "changed=false"
  out "previous_commit="
  exit 0
fi

previous=$(sed -n 's/^commit: *//p' "$data_dir/claude-memory-map.yml" 2>/dev/null | head -1 || true)
out "previous_commit=${previous}"

commit_date=$(git -C "$here" show -s --format=%cI "$SOURCE_COMMIT")

git -C "$SITE_DIR" checkout -B "$BRANCH"

cp "$here/index.html" "$asset_dir/index.html"
mkdir -p "$data_dir"
{
  echo "# Provenance of the vendored copy at assets/tools/claude-memory-map/."
  echo "# Maintained by the source repo's site-sync/site-preview workflows"
  echo "# (github.com/Adam-S-Daniel/claude-memory-map) — don't hand-edit."
  echo "repo: Adam-S-Daniel/claude-memory-map"
  echo "ref: ${SOURCE_REF}"
  echo "commit: ${SOURCE_COMMIT}"
  echo "source_committed_at: ${commit_date}"
  if [ -n "${SOURCE_PR:-}" ]; then
    echo "source_pr: ${SOURCE_PR}"
  fi
} >"$data_dir/claude-memory-map.yml"

if [ -n "$(git -C "$SITE_DIR" status --porcelain)" ]; then
  git -C "$SITE_DIR" add assets/tools/claude-memory-map _data/tool_sources
  git -C "$SITE_DIR" \
    -c user.name="github-actions[bot]" \
    -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
    commit -m "$COMMIT_MSG"
  git -C "$SITE_DIR" push -f origin "$BRANCH"
  out "changed=true"
else
  echo "Site already has this content — nothing to push."
  out "changed=false"
fi
