#!/bin/sh
# Runs this Exercise's check. Exit code 0 means every check passed.
cd "$(dirname "$0")" || exit 2
target=4.7.2
have=$(godot --version 2>/dev/null) || { echo "godot not found on PATH"; exit 2; }
case "$have" in
  "$target".*) ;;
  *) echo "warning: this Exercise targets Godot $target; you have $have" ;;
esac
godot --headless --import --path . >/dev/null 2>&1
exec godot --headless --fixed-fps 60 --path . -s check/check.gd 2>/dev/null
