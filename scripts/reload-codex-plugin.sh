#!/usr/bin/env bash
set -euo pipefail

# Refresh the configured Praxis marketplace and replace the installed package.
# Honor an explicit override, then PATH, then the macOS app-bundled CLI.
codex_bin="${CODEX_BIN:-}"
if [[ -z "$codex_bin" ]]; then
  codex_bin="codex"
  if ! command -v "$codex_bin" >/dev/null 2>&1; then
    for app_root in /Applications "$HOME/Applications"; do
      candidate="$app_root/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
      if [[ -x "$candidate" ]]; then
        codex_bin="$candidate"
        break
      fi
    done
  fi
fi
if ! command -v "$codex_bin" >/dev/null 2>&1; then
  echo "Codex CLI not found. Add codex to PATH or set CODEX_BIN to its executable." >&2
  exit 1
fi

"$codex_bin" plugin marketplace upgrade praxis
"$codex_bin" plugin add praxis@praxis

echo 'Praxis plugin package refreshed.'
echo 'Open a new chat to load the updated skills. If Praxis is still missing, restart Codex.'
echo 'This does not reload the current chat or enable Praxis in the project.'
