# CliClip 🚀

**CliClip** is a lightweight, context-aware clipboard enhancement tool for macOS developers. It automatically detects when you are in a terminal environment and converts clipboard images into file paths (prefixed with `@`), making it perfect for using with multi-modal AI CLIs or terminal workflows.

## ✨ Features

- **Context-Aware**: Automatically converts images to paths in **iTerm2** and **Terminal**.
- **Auto-Restore**: Switches back to the original image data when you move to GUI apps (WeChat, Chrome, Slack, etc.).
- **Smart Filtering**: Ignores file copies and rich-text/HTML copies to prevent workflow interference.
- **Zero Dependencies**: Pure Python + Native macOS tools (`osascript`, `sips`, `perl`).
- **Optimized for AI**: Automatically resizes large images to 1280px to save LLM tokens and speed up uploads.

## 🛠 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/CliClip.git
   cd CliClip
   ```
2. Run the installation script:
   ```bash
   bash scripts/install.sh
   ```
3. **Grant Permissions**: When you first copy an image and switch to your terminal, macOS will ask for permission to allow the terminal to control "System Events". Click **Allow**.

## 📖 Usage

1. **Take a screenshot** (e.g., via WeChat or System shortcut).
2. **Switch to iTerm2/Terminal**.
3. **Paste (Cmd+V)**: You will see something like `@/tmp/cliclip_temp_img.png`.
4. **Switch to WeChat**: Paste (Cmd+V) will still paste the original image.

## 🗑 Uninstallation

```bash
launchctl unload ~/Library/LaunchAgents/com.cliclip.daemon.plist
rm ~/Library/LaunchAgents/com.cliclip.daemon.plist
rm -rf ~/.cliclip
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
