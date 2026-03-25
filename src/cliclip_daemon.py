import os
import signal
import subprocess
import sys
import threading
import time

# --- Configuration ---
TEMP_IMAGE_DIR = "/tmp/.cc"
TEMP_IMAGE_PREFIX = "cc"
MAX_DIMENSION = 1280
MAX_SAVED_IMAGES = 20
TERMINAL_APPS = ["iTerm2", "iTerm", "Terminal"]
POLL_INTERVAL = 0.2

saved_image_paths = []
saved_image_paths_lock = threading.Lock()


def encode_base36(num):
    """Encodes a positive integer using a short base36 string."""
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    if num <= 0:
        return "0"

    chars = []
    while num:
        num, remainder = divmod(num, 36)
        chars.append(alphabet[remainder])
    return "".join(reversed(chars))


def ensure_temp_dir():
    """Creates the hidden temp directory when needed."""
    try:
        os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)
        return True
    except:
        return False


def build_image_path():
    """Builds a timestamp-based path for a saved clipboard image."""
    if not ensure_temp_dir():
        return None

    while True:
        timestamp = encode_base36(time.time_ns() // 1_000)
        image_path = os.path.join(TEMP_IMAGE_DIR, f"{TEMP_IMAGE_PREFIX}_{timestamp}.png")
        if not os.path.exists(image_path):
            return image_path
        time.sleep(0.001)


def append_saved_image_path(image_path):
    """Appends a newly captured image path to the rolling history."""
    paths_to_remove = []
    with saved_image_paths_lock:
        saved_image_paths.append(image_path)
        while len(saved_image_paths) > MAX_SAVED_IMAGES:
            paths_to_remove.append(saved_image_paths.pop(0))

    for old_path in paths_to_remove:
        remove_file_if_exists(old_path)
        remove_file_if_exists(f"{old_path}.resize")


def get_latest_saved_image_path():
    """Returns the newest existing saved image path, pruning stale entries."""
    with saved_image_paths_lock:
        while saved_image_paths:
            latest_path = saved_image_paths[-1]
            if os.path.exists(latest_path):
                return latest_path
            saved_image_paths.pop()
    return None


def remove_file_if_exists(path):
    """Best-effort removal for temporary files."""
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass


def clear_saved_images():
    """Clears the saved image history and deletes its temp files."""
    with saved_image_paths_lock:
        paths_to_remove = list(saved_image_paths)
        saved_image_paths.clear()

    for image_path in paths_to_remove:
        remove_file_if_exists(image_path)
        remove_file_if_exists(f"{image_path}.resize")

    # Remove legacy single-image files if they exist from older versions.
    remove_file_if_exists(os.path.join(TEMP_IMAGE_DIR, f"{TEMP_IMAGE_PREFIX}.png"))
    remove_file_if_exists(os.path.join(TEMP_IMAGE_DIR, "cliclip_temp_img.png"))
    remove_file_if_exists(os.path.join("/tmp", f"{TEMP_IMAGE_PREFIX}.png"))
    remove_file_if_exists(os.path.join("/tmp", "cliclip_temp_img.png"))

    try:
        if os.path.isdir(TEMP_IMAGE_DIR) and not os.listdir(TEMP_IMAGE_DIR):
            os.rmdir(TEMP_IMAGE_DIR)
    except:
        pass


def get_frontmost_app():
    """Returns the name of the application currently in focus."""
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    try:
        res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        return res.stdout.strip()
    except:
        return ""


def get_clipboard_info():
    """Returns basic clipboard metadata (types of data present)."""
    try:
        res = subprocess.run(['osascript', '-e', 'get (clipboard info)'], capture_output=True, text=True)
        return res.stdout
    except:
        return ""


def is_pure_image(info):
    """Checks if the clipboard contains image data but not file operations."""
    has_image = "PNG" in info or "picture" in info
    is_file_op = "furl" in info or "filenames" in info
    return has_image and not is_file_op


def resize_image_async(image_path):
    """Resizes a saved image in the background so path availability is not blocked."""
    resized_path = f"{image_path}.resize"
    try:
        subprocess.run(
            ['cp', image_path, resized_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        subprocess.run(
            ['sips', '-Z', str(MAX_DIMENSION), resized_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if os.path.exists(resized_path) and os.path.getsize(resized_path) > 0:
            os.replace(resized_path, image_path)
            resized_path = None
    except:
        pass
    finally:
        remove_file_if_exists(resized_path)


def save_image_binary():
    """Extracts clipboard image data to a unique file and starts background optimization."""
    image_path = build_image_path()
    if not image_path:
        return False
    cmd = f"osascript -e 'get the clipboard as «class PNGf»' | perl -ne 'print pack(\"H*\", substr($_, 11, -1))' > {image_path}"
    try:
        remove_file_if_exists(image_path)
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
            append_saved_image_path(image_path)
            threading.Thread(target=resize_image_async, args=(image_path,), daemon=True).start()
            return True
    except:
        pass
    return False


def set_path_clipboard():
    """Copies the newest image marker to the clipboard for terminal pasting."""
    latest_image_path = get_latest_saved_image_path()
    if not latest_image_path or not os.path.exists(latest_image_path):
        return False
    try:
        subprocess.run(['pbcopy'], input=latest_image_path, text=True, stderr=subprocess.DEVNULL, check=False)
        return True
    except:
        return False


def restore_image_to_clipboard():
    """Restores the newest saved image back to the system clipboard."""
    latest_image_path = get_latest_saved_image_path()
    if not latest_image_path or not os.path.exists(latest_image_path):
        return False

    script = f'set the clipboard to (read (POSIX file "{latest_image_path}") as «class PNGf»)'
    try:
        subprocess.run(['osascript', '-e', script], stderr=subprocess.DEVNULL, check=False)
        return True
    except:
        return False


def cleanup(sig, frame):
    """Cleanup temporary files on exit."""
    clear_saved_images()
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
                else:
                    if current_mode != "TEXT":
                        current_mode = "TEXT"

            if curr_app in TERMINAL_APPS:
                if current_mode == "IMAGE" and (app_changed or clipboard_changed):
                    if set_path_clipboard():
                        current_mode = "PATH"
                        time.sleep(0.05)
                        curr_info = get_clipboard_info()
            elif app_changed and current_mode == "PATH":
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
