<h1 align="center">CliClip</h1>

<p align="center">
  <strong>Your clipboard bridge for terminal AI workflows.</strong><br />
  Paste images as short <code>@/tmp/.cc/...</code> paths in terminal, restore the original image in GUI apps.
</p>

<p align="center">
  <strong><a href="#english">English</a></strong> ·
  <strong><a href="#zh">中文</a></strong>
</p>

---

<a id="english"></a>
## English

**CliClip** detects when you switch into `iTerm2` or `Terminal` and turns the current clipboard image into a short file path like `@/tmp/.cc/cc_h8x2w9k3zl.png`. When you switch back to GUI apps such as WeChat, Chrome, or Slack, it restores the original image to the clipboard.

### Features

- Context-aware image-to-path conversion in `iTerm2`, `iTerm`, and `Terminal`
- Unique temp file per image, so later screenshots do not overwrite earlier pasted paths
- Hidden temp directory with short path output, such as `@/tmp/.cc/cc_h8x2w9k3zl.png`
- Automatic image restore when you leave the terminal
- Smart filtering to avoid interfering with file copies or rich text clipboard content
- No extra dependencies beyond macOS native tools and `/usr/bin/python3`
- Automatic downscaling of large images to `1280px` to reduce upload size and token usage

### Installation

Run the installation script:

```bash
curl -fsSL https://raw.githubusercontent.com/ErzhanChen/CliClip/main/scripts/install.sh | bash
```

The installer will:

- Download the latest daemon script
- Install it into `~/.cliclip`
- Register and start the macOS LaunchAgent automatically

When you first copy an image and switch to your terminal, macOS may ask for permission to let your terminal control `System Events`. Click `Allow`.

### Usage

1. Copy or screenshot an image.
2. Switch to `iTerm2` or `Terminal`.
3. Paste with `Cmd+V`.
4. CliClip will paste the latest image path, for example `@/tmp/.cc/cc_h8x2w9k3zl.png`.
5. Switch back to a GUI app and paste again to get the original image.

Notes:

- CliClip keeps up to `20` temp images at a time.
- Older temp files are deleted first when the limit is exceeded.
- Temp files are cleared when you copy non-image content or when the daemon exits.

### Uninstallation

```bash
launchctl unload ~/Library/LaunchAgents/com.cliclip.daemon.plist
rm ~/Library/LaunchAgents/com.cliclip.daemon.plist
rm -rf ~/.cliclip
```

<a id="zh"></a>
## 简体中文

**CliClip** 是一个面向 macOS 终端工作流的轻量级剪贴板增强工具。当前台应用切换到 `iTerm2` 或 `Terminal` 时，它会把剪贴板中的图片自动转换成短路径，例如 `@/tmp/.cc/cc_h8x2w9k3zl.png`；切回微信、Chrome、Slack 等图形界面应用后，又会把原始图片恢复回剪贴板。

### 功能特性

- 在 `iTerm2`、`iTerm` 和 `Terminal` 中自动把图片转换为路径
- 每张图片都会生成独立的临时文件，后续截图不会覆盖之前已经粘贴出的路径
- 临时图片保存在隐藏目录中，输出路径简短，例如 `@/tmp/.cc/cc_h8x2w9k3zl.png`
- 离开终端后会自动恢复原始图片内容
- 智能过滤文件复制、富文本和 HTML 等剪贴板内容，避免误干扰
- 不依赖额外运行时，只使用 macOS 原生工具和 `/usr/bin/python3`
- 大图会自动压缩到 `1280px`，减少上传体积和模型 token 消耗

### 安装方式

直接运行安装脚本即可：

```bash
curl -fsSL https://raw.githubusercontent.com/ErzhanChen/CliClip/main/scripts/install.sh | bash
```

安装脚本会自动完成以下操作：

- 下载最新的守护进程脚本
- 安装到 `~/.cliclip`
- 自动注册并启动 macOS LaunchAgent

第一次复制图片并切换到终端时，macOS 可能会弹出权限提示，请允许终端控制 `System Events`。

### 使用方法

1. 复制一张图片，或者先截图。
2. 切换到 `iTerm2` 或 `Terminal`。
3. 按 `Cmd+V` 粘贴。
4. CliClip 会粘贴最新图片对应的路径，例如 `@/tmp/.cc/cc_h8x2w9k3zl.png`。
5. 再切回图形界面应用粘贴时，会恢复为原始图片内容。

说明：

- CliClip 最多会保留 `20` 张临时图片。
- 超过上限后，会优先删除最旧的临时文件。
- 当你复制非图片内容，或守护进程退出时，临时文件会被清理。

### 卸载

```bash
launchctl unload ~/Library/LaunchAgents/com.cliclip.daemon.plist
rm ~/Library/LaunchAgents/com.cliclip.daemon.plist
rm -rf ~/.cliclip
```

## License

MIT. See [LICENSE](LICENSE).
