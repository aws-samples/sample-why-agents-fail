#!/usr/bin/env bash
# Render the conversation-management diagrams from their editable D2 source.
#
# Both diagrams ship as ready-to-use SVG (renders directly in GitHub and browsers)
# plus editable D2 source. Run this script to also produce PNGs for the README/blog.
#
# Requirements:
#   - d2           (brew install d2)      -> renders the .d2 source to SVG/PNG
#   - rsvg-convert (brew install librsvg) -> optional, SVG -> PNG fallback
set -euo pipefail
cd "$(dirname "$0")"

for name in conversation-management-strategies recall-probe-flow; do
  echo "== $name =="
  if command -v d2 >/dev/null 2>&1; then
    d2 --layout dagre "$name.d2" "$name.svg"
    d2 --layout dagre "$name.d2" "$name.png"
    echo "  wrote $name.svg and $name.png (from D2)"
  elif command -v rsvg-convert >/dev/null 2>&1 && [ -f "$name.svg" ]; then
    rsvg-convert -z 2 "$name.svg" -o "$name.png"
    echo "  wrote $name.png (from SVG)"
  else
    echo "  skip: install d2 or rsvg-convert to render (SVG source, if present, is usable)"
  fi
done

echo "Done."
