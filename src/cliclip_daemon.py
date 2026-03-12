import subprocess
import time
import os
import signal
import sys
import threading
import shutil

# --- Configuration ---
TEMP_IMAGE_PATH = "/tmp/cliclip_temp_img.png"
CLIP_MARKER = f"@{TEMP_IMAGE_PATH}"
MAX_DIMENSION = 1280
# Added "iTerm" for compatibility with different versions/settings
TERMINAL_APPS = ["iTerm2", "iTerm", "Terminal"]
POLL_INTERVAL = 0.2

latest_image_token = 0
latest_image_token_lock = threading.Lock()


def next_image_token():
    """Returns a monotonically increasing token for saved clipboard images."""
    global latest_image_token
    with latest_image_token_lock:
        latest_image_token += 1
        return latest_image_token


def is_latest_image_token(token):
    """Checks whether a background task still targets the newest saved image."""
    with latest_image_token_lock:
        return token == latest_image_token

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
    """Checks if the clipboard contains image data but not file operations."""
    has_image = "PNG" in info or "picture" in info
    is_file_op = "furl" in info or "filenames" in info
    # We relaxed the text check to ensure screenshots with minor metadata are captured
    return has_image and not is_file_op


def resize_image_async(image_token):
    """Resizes the saved image in the background so path availability is not blocked."""
    resized_path = f"{TEMP_IMAGE_PATH}.{image_token}.resize"
    try:
        shutil.copyfile(TEMP_IMAGE_PATH, resized_path)
        subprocess.run(
            ['sips', '-Z', str(MAX_DIMENSION), resized_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if not is_latest_image_token(image_token):
            return
        if os.path.exists(resized_path) and os.path.getsize(resized_path) > 0:
            os.replace(resized_path, TEMP_IMAGE_PATH)
            resized_path = None
    except:
        pass
    finally:
        if resized_path and os.path.exists(resized_path):
            try:
                os.remove(resized_path)
            except:
                pass


def save_image_binary():
    """Extracts clipboard image data to disk and starts background optimization."""
    cmd = f"osascript -e 'get the clipboard as «class PNGf»' | perl -ne 'print pack(\"H*\", substr($_, 11, -1))' > {TEMP_IMAGE_PATH}"
    try:
        if os.path.exists(TEMP_IMAGE_PATH):
            os.remove(TEMP_IMAGE_PATH)
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if os.path.exists(TEMP_IMAGE_PATH) and os.path.getsize(TEMP_IMAGE_PATH) > 0:
            image_token = next_image_token()
            threading.Thread(target=resize_image_async, args=(image_token,), daemon=True).start()
            return True
    except:
        pass
    return False


def set_path_clipboard():
    """Copies the image path marker to the clipboard for terminal pasting."""
    try:
        subprocess.run(['pbcopy'], input=CLIP_MARKER, text=True, stderr=subprocess.DEVNULL, check=False)
        return True
    except:
        return False

def restore_image_to_clipboard():
    """Restores the previously saved image data back to the system clipboard."""
    script = f'set the clipboard to (read (POSIX file "{TEMP_IMAGE_PATH}") as «class PNGf»)'
    try:
        subprocess.run(['osascript', '-e', script], stderr=subprocess.DEVNULL, check=False)
        return True
    except:
        return False

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
            app_changed = curr_app != last_app
            clipboard_changed = curr_info != last_info

            if clipboard_changed:
                if is_pure_image(curr_info):
                    if save_image_binary():
                        current_mode = "IMAGE"
                elif current_mode != "TEXT":
                    current_mode = "TEXT"

            if curr_app in TERMINAL_APPS:
                if current_mode == "IMAGE" and os.path.exists(TEMP_IMAGE_PATH) and (app_changed or clipboard_changed):
                    if set_path_clipboard():
                        current_mode = "PATH"
                        time.sleep(0.05)
                        curr_info = get_clipboard_info()
            elif app_changed and current_mode == "PATH" and os.path.exists(TEMP_IMAGE_PATH):
                if restore_image_to_clipboard():
                    current_mode = "IMAGE"
                    time.sleep(0.05)
                    curr_info = get_clipboard_info()

            last_app = curr_app
            last_info = curr_info
            time.sleep(POLL_INTERVAL)
        except:
            time.sleep(2)

if __name__ == "__main__":
    main()
