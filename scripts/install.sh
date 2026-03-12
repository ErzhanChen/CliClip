#!/bin/bash

APP_NAME="CliClip"
INSTALL_DIR="$HOME/.cliclip"
PLIST_LABEL="com.cliclip.daemon"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"
SCRIPT_SOURCE_PATH="$(dirname "$0")/../src/cliclip_daemon.py"
SCRIPT_DEST_PATH="$INSTALL_DIR/cliclip_daemon.py"

echo "------------------------------------------------"
echo "🚀 Installing $APP_NAME..."
echo "------------------------------------------------"

# 1. Create directory
mkdir -p "$INSTALL_DIR"

# 2. Copy source script
cp "$SCRIPT_SOURCE_PATH" "$SCRIPT_DEST_PATH"

# 3. Create LaunchAgent .plist
cat << EOF > "$PLIST_PATH"
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

# 4. Load and Start
pkill -f cliclip_daemon.py 2>/dev/null
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

echo "------------------------------------------------"
echo "✅ $APP_NAME installed successfully!"
echo "------------------------------------------------"
echo "Features:"
echo " - Image -> @Path (auto conversion when in iTerm2/Terminal)"
echo " - Auto Image Restore (when in WeChat, Chrome, etc.)"
echo " - Native Performance, No Dependencies"
echo "------------------------------------------------"
