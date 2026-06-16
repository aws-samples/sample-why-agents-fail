#!/usr/bin/env bash
# Render the context-offloader diagrams to PNG.
#
# Both diagrams ship as ready-to-use SVG (renders directly in GitHub and browsers)
# plus editable source (D2 for the flow diagram, draw.io XML for the architecture).
# Run this script to also produce PNGs for the blog/README.
#
# Requirements (install what you have):
#   - d2          (brew install d2)         -> renders the .d2 source
#   - rsvg-convert(brew install librsvg)    -> converts .svg -> .png
#   - drawio CLI  (brew install --cask drawio) -> renders the .drawio source
set -euo pipefail
cd "$(dirname "$0")"

echo "== Diagram A: Native ContextOffloader flow =="
if command -v d2 >/dev/null 2>&1; then
  # Render straight from the editable D2 source to PNG
  d2 --layout dagre native-context-offloader-flow.d2 native-context-offloader-flow.png
  echo "  wrote native-context-offloader-flow.png (from D2)"
elif command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -z 2 native-context-offloader-flow.svg -o native-context-offloader-flow.png
  echo "  wrote native-context-offloader-flow.png (from SVG)"
else
  echo "  skip: install d2 or rsvg-convert to produce PNG (SVG already usable)"
fi

echo "== Diagram B: AgentCore two-memories architecture =="
DRAWIO_BIN=""
for c in drawio "/Applications/draw.io.app/Contents/MacOS/draw.io" "$HOME/Downloads/draw.io.app/Contents/MacOS/draw.io"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then DRAWIO_BIN="$c"; break; fi
done
if [ -n "$DRAWIO_BIN" ]; then
  "$DRAWIO_BIN" --export --format png --scale 2 --border 12 \
    --output agentcore-two-memories-architecture.png \
    agentcore-two-memories-architecture.drawio
  echo "  wrote agentcore-two-memories-architecture.png (from draw.io, AWS4 icons)"
elif command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -z 2 agentcore-two-memories-architecture.svg -o agentcore-two-memories-architecture.png
  echo "  wrote agentcore-two-memories-architecture.png (from SVG)"
else
  echo "  skip: install drawio CLI or rsvg-convert to produce PNG (SVG already usable)"
fi

echo "Done."
