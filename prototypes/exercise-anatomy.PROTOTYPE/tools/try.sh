#!/bin/sh
# Runs an Exercise's check on a temporary copy with reference files swapped in, so the starter stays untouched.
# Usage: tools/try.sh <exercise dir> <file in exercise>=<replacement> ...
ex=$1; shift
tmp=$(mktemp -d)
cp -r "$ex"/. "$tmp"/
for pair in "$@"; do cp "${pair#*=}" "$tmp/${pair%%=*}"; done
"$tmp/check.sh"; code=$?
rm -rf "$tmp"
exit $code
