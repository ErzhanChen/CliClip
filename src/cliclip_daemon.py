import subprocess
import time
import os
import signal
import sys

# --- Configuration ---
TEMP_IMAGE_PATH = "/tmp/cliclip_temp_img.png"
CLIP_MARKER = f"@{TEMP_IMAGE_PATH}"
MAX_DIMENSION = 1280
TERMINAL_APPS = ["iTerm2", "Terminal"]
POLL_INTERVAL = 0.5 

def get_frontmost_app():
    """Returns the name of the application currently in focus."""
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    try:
        res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        return res.stdout.strip()
    except: return ""

def get_clipboard_info():
    """Returns basic clipboard metadata (types of data present)."""
    try:
        res = subprocess.run(['osascript', '-e', 'get (clipboard info)'], capture_output=True, text=True)
        return res.stdout
    except: return ""

def is_pure_image(info):
    """Checks if the clipboard contains image data but not file or rich text data."""
    has_image = "PNG" in info or "picture" in info
    is_file_op = "furl" in info or "filenames" in info
    has_text = "Unicode text" in info or "string" in info
    return has_image and not is_file_op and not has_text

def save_image_binary():
    """Extracts binary image data from clipboard and saves to file via Perl hack."""
    cmd = f"osascript -e 'get the clipboard as «class PNGf»' | perl -ne 'print pack(\"H*\", substr($_, 11, -1))' > {TEMP_IMAGE_PATH}"
    try:
        if os.path.exists(TEMP_IMAGE_PATH): os.remove(TEMP_IMAGE_PATH)
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
        if os.path.exists(TEMP_IMAGE_PATH) and os.path.getsize(TEMP_IMAGE_PATH) > 0:
            # Resize image to save tokens and optimize multi-modal AI inputs
            subprocess.run(['sips', '-Z', str(MAX_DIMENSION), TEMP_IMAGE_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    except: pass
    return False

def restore_image_to_clipboard():
    """Restores the previously saved image data back to the system clipboard."""
    script = f'set the clipboard to (read (POSIX file "{TEMP_IMAGE_PATH}") as «class PNGf»)'
    try:
        subprocess.run(['osascript', '-e', script], stderr=subprocess.DEVNULL)
        return True
    except: return False

def cleanup(sig, frame):
    """Cleanup temporary files on exit."""
    if os.path.exists(TEMP_IMAGE_PATH):
        try: os.remove(TEMP_IMAGE_PATH)
        except: pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    """Main loop for context-aware clipboard management."""
    last_info = get_clipboard_info()
    last_app = get_frontmost_app()
    current_mode = "IMAGE" if is_pure_image(last_info) else "TEXT"
    
    while True:
        try:
            curr_app = get_frontmost_app()
            curr_info = get_clipboard_info()
            
            # Detect new screenshots
            if (curr_info != last_info) and is_pure_image(curr_info):
                if save_image_binary(): current_mode = "IMAGE"
                last_info = curr_info
            
            # Detect context switching (Terminals vs GUI Apps)
            if curr_app != last_app or (curr_info != last_info and current_mode != "TEXT"):
                if curr_app in TERMINAL_APPS:
                    if current_mode == "IMAGE":
                        subprocess.run(['pbcopy'], input=CLIP_MARKER, text=True)
                        current_mode = "PATH"
                        time.sleep(0.1)
                        last_info = get_clipboard_info()
                elif curr_app not in TERMINAL_APPS:
                    if current_mode == "PATH" and os.path.exists(TEMP_IMAGE_PATH):
                        if restore_image_to_clipboard():
                            current_mode = "IMAGE"
                            time.sleep(0.1)
                            last_info = get_clipboard_info()
            
            last_app = curr_app
            time.sleep(POLL_INTERVAL)
        except: time.sleep(2)

if __name__ == "__main__":
    main()
