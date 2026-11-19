# Sourced by setup and threads, so a fix to how they pick their repo is made
# once. Needs git and gh. Written for Bash 3.2, macOS's /bin/bash.
# shellcheck shell=bash

# resolve_repo <script>: prints owner/name of the repo behind the `origin`
# remote, or $GH_REPO if set, and fails with an error naming <script> if
# there's neither. It never lets gh pick a remote, because gh prefers an
# `upstream` remote over `origin`, and in a Derived repo `upstream` can point
# at the Template.
resolve_repo() {
  local origin
  if [[ -n ${GH_REPO:-} ]]; then
    # gh also takes HOST/OWNER/REPO, but callers split the value into owner
    # and name, and a host can't reach the caller's environment from here.
    if [[ $GH_REPO == */*/* ]]; then
      echo "$1: GH_REPO must be owner/name; set the host in GH_HOST" >&2
      return 1
    fi
    echo "$GH_REPO"
  elif origin=$(git remote get-url origin 2>/dev/null); then
    gh repo view "$origin" --json nameWithOwner --jq .nameWithOwner
  else
    echo "$1: no origin remote, so set GH_REPO=owner/name to choose the repo" >&2
    return 1
  fi
}
