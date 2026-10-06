#!/usr/bin/env bash
set -euo pipefail

# Refresh the configured Praxis marketplace and replace the installed package.
# CODEX_BIN may point to the app-bundled CLI when codex is not on PATH.
codex_bin="${CODEX_BIN:-codex}"
if ! command -v "$codex_bin" >/dev/null 2>&1; then
  echo "Codex CLI not found. Add codex to PATH or set CODEX_BIN to its executable." >&2
  exit 1
fi

"$codex_bin" plugin marketplace upgrade praxis
"$codex_bin" plugin add praxis@praxis

echo 'Praxis plugin package refreshed.'
echo 'Open a new chat to load the updated skills. If Praxis is still missing, restart Codex.'
echo 'This does not reload the current chat or enable Praxis in the project.'
