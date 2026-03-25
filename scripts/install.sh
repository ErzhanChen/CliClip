#!/bin/bash

set -euo pipefail

APP_NAME="CliClip"
INSTALL_DIR="$HOME/.cliclip"
PLIST_LABEL="com.cliclip.daemon"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/$PLIST_LABEL.plist"
SCRIPT_DEST_PATH="$INSTALL_DIR/cliclip_daemon.py"

REPO_OWNER="${CLICLIP_REPO_OWNER:-ErzhanChen}"
REPO_NAME="${CLICLIP_REPO_NAME:-CliClip}"
REPO_REF="${CLICLIP_REPO_REF:-main}"
RAW_BASE_URL="${CLICLIP_RAW_BASE_URL:-https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/$REPO_REF}"
REMOTE_SCRIPT_URL="$RAW_BASE_URL/src/cliclip_daemon.py"
LOCAL_SCRIPT_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../src/cliclip_daemon.py"
SKIP_LAUNCHD="${CLICLIP_SKIP_LAUNCHD:-0}"

print_header() {
    echo "------------------------------------------------"
    echo "Installing $APP_NAME..."
    echo "------------------------------------------------"
}

require_macos() {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        echo "$APP_NAME only supports macOS."
        exit 1
    fi
}

download_file() {
    local url="$1"
    local dest="$2"

    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$dest"
        return 0
    fi

    if command -v wget >/dev/null 2>&1; then
        wget -qO "$dest" "$url"
        return 0
    fi

    echo "Neither curl nor wget is available, so the installer cannot download files."
    exit 1
}

install_daemon_script() {
    mkdir -p "$INSTALL_DIR"

    if [[ -f "$LOCAL_SCRIPT_SOURCE" ]]; then
        cp "$LOCAL_SCRIPT_SOURCE" "$SCRIPT_DEST_PATH"
        return 0
    fi

    echo "Fetching daemon from $REMOTE_SCRIPT_URL"
    download_file "$REMOTE_SCRIPT_URL" "$SCRIPT_DEST_PATH"
}

write_launch_agent() {
    mkdir -p "$PLIST_DIR"

    cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$SCRIPT_DEST_PATH</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/cliclip.err</string>
</dict>
</plist>
EOF
}

reload_launch_agent() {
    if [[ "$SKIP_LAUNCHD" == "1" ]]; then
        echo "Skipping LaunchAgent reload because CLICLIP_SKIP_LAUNCHD=1"
        return 0
    fi

    pkill -f cliclip_daemon.py 2>/dev/null || true
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"
}

print_success() {
    echo "------------------------------------------------"
    echo "$APP_NAME installed successfully."
    echo "------------------------------------------------"
    echo "Features:"
    echo " - Image -> Path when the frontmost app is iTerm2 or Terminal"
    echo " - Original image restored automatically in GUI apps"
    echo " - No extra dependencies required"
    echo
    echo "If prompted, allow your terminal to control System Events."
}

main() {
    print_header
    require_macos
    install_daemon_script
    write_launch_agent
    reload_launch_agent
    print_success
}

main "$@"
