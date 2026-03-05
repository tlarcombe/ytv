#!/usr/bin/env bash
# ytv installer
# Installs ytv and its dependencies (mpv, fzf, yt-dlp) and symlinks
# the script to ~/.local/bin/ytv.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_BIN="$HOME/.local/bin"
INSTALL_TARGET="$INSTALL_BIN/ytv"

# ─── Colours ──────────────────────────────────────────────────────────────────
RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; RST=$'\033[0m'
ok()   { echo "${GRN}✓${RST} $*"; }
warn() { echo "${YLW}!${RST} $*"; }
err()  { echo "${RED}✗${RST} $*" >&2; exit 1; }

# ─── Detect package manager ───────────────────────────────────────────────────
install_pkg() {
    local pkg="$1"
    if command -v pacman &>/dev/null; then
        echo "  → sudo pacman -S --noconfirm $pkg"
        sudo pacman -S --noconfirm "$pkg"
    elif command -v apt &>/dev/null; then
        echo "  → sudo apt install -y $pkg"
        sudo apt install -y "$pkg"
    elif command -v dnf &>/dev/null; then
        echo "  → sudo dnf install -y $pkg"
        sudo dnf install -y "$pkg"
    else
        warn "No supported package manager found. Please install $pkg manually."
        return 1
    fi
}

# ─── Check / install dependency ───────────────────────────────────────────────
check_dep() {
    local cmd="$1"
    local pkg="${2:-$1}"
    if command -v "$cmd" &>/dev/null; then
        ok "$cmd ($(command -v "$cmd"))"
    else
        warn "$cmd not found — installing $pkg..."
        if install_pkg "$pkg"; then
            ok "$cmd installed"
        fi
    fi
}

# ─── Main ─────────────────────────────────────────────────────────────────────
echo "=== ytv installer ==="
echo

echo "Checking dependencies..."
check_dep python3 python
check_dep fzf
check_dep mpv
check_dep yt-dlp
echo

echo "Installing ytv..."
mkdir -p "$INSTALL_BIN"

# Symlink so 'git pull' in the repo gives you updates automatically
if [[ -L "$INSTALL_TARGET" ]] || [[ -f "$INSTALL_TARGET" ]]; then
    rm -f "$INSTALL_TARGET"
fi
ln -s "$SCRIPT_DIR/ytv" "$INSTALL_TARGET"
chmod +x "$SCRIPT_DIR/ytv"
ok "ytv → $INSTALL_TARGET"
echo

# ─── PATH check ───────────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$INSTALL_BIN:"* ]]; then
    warn "$INSTALL_BIN is not in your \$PATH."
    echo "  Add one of the following to your shell rc file:"
    echo
    echo "    # ~/.zshrc or ~/.bashrc"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo
    SHELL_RC=""
    if [[ -f "$HOME/.zshrc" ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    if [[ -n "$SHELL_RC" ]]; then
        read -r -p "  Add it to $SHELL_RC now? [y/N] " answer
        if [[ "${answer,,}" == "y" ]]; then
            echo '' >> "$SHELL_RC"
            echo '# ytv' >> "$SHELL_RC"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
            ok "Added to $SHELL_RC — restart your shell or: source $SHELL_RC"
        fi
    fi
    echo
fi

# ─── FreeTube check ───────────────────────────────────────────────────────────
FREETUBE_DB="${XDG_CONFIG_HOME:-$HOME/.config}/FreeTube/profiles.db"
if [[ -f "$FREETUBE_DB" ]]; then
    NSUBS=$(python3 -c "
import json, sys
with open('$FREETUBE_DB') as f:
    content = f.read()
subs = []
for line in content.strip().splitlines():
    try:
        obj = json.loads(line)
        if isinstance(obj.get('subscriptions'), list):
            subs.extend(obj['subscriptions'])
    except Exception:
        pass
ids = set(s['id'] for s in subs if s.get('id'))
print(len(ids))
" 2>/dev/null || echo "?")
    ok "FreeTube database found: $FREETUBE_DB ($NSUBS subscriptions)"
else
    warn "FreeTube database not found at $FREETUBE_DB"
    echo "  If FreeTube is installed elsewhere, set the path in:"
    echo "  ${XDG_CONFIG_HOME:-$HOME/.config}/ytv/config.json"
fi
echo

echo "=== Done! ==="
echo
echo "Run 'ytv' to start, or 'ytv --help' for options."
echo "First run fetches all feeds — this may take ~10–20s."
echo "Subsequent runs use a 1-hour cache, so startup is instant."
