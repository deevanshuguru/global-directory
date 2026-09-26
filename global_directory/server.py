"""
server.py — Global Directory
Handles file serving, directory listing, static assets, and file preview.
Extends Python's built-in SimpleHTTPRequestHandler — security and file
serving are handled natively. We only override list_directory (custom UI)
and add two new routes: /static/ and /preview/.
"""

import os, io, json, mimetypes, datetime, http.server
from urllib.parse import unquote, urlparse


# ── Package location ──────────────────────────────────────────────────────────
# Used to locate templates/ and static/ directories relative to this file.
# Works correctly for both editable installs and PyPI installs.
PKG_DIR = os.path.dirname(os.path.abspath(__file__))


# ── File type mappings ────────────────────────────────────────────────────────
# Maps file extensions to a category name used for filtering in the UI.
TYPE_MAP = {
    "image":    {".jpg",".jpeg",".png",".gif",".webp",".svg",".ico",".bmp",".tiff"},
    "video":    {".mp4",".avi",".mov",".mkv",".wmv",".flv",".webm",".m4v"},
    "audio":    {".mp3",".wav",".flac",".aac",".ogg",".m4a",".wma"},
    "document": {".pdf",".doc",".docx",".txt",".md",".rtf",".odt",".ppt",".pptx"},
    "code":     {".py",".js",".ts",".html",".css",".json",".xml",".yaml",".yml",
                 ".toml",".ini",".sh",".bash",".zsh",".rb",".go",".rs",".c",
                 ".cpp",".h",".java",".kt",".swift",".php",".sql",".vue",
                 ".jsx",".tsx",".r",".env",".dockerfile",".conf",".cfg",".log"},
    "data":     {".csv",".xlsx",".xls",".db",".sqlite",".parquet"},
    "archive":  {".zip",".tar",".gz",".rar",".7z",".bz2",".xz",".dmg",".iso"},
}

# Accent colors per type — used in the UI for badges and icons.
COLORS = {
    "folder":"#f59e0b","image":"#8b5cf6","video":"#ef4444","audio":"#ec4899",
    "document":"#3b82f6","code":"#10b981","data":"#f97316","archive":"#6366f1","file":"#94a3b8",
}

# Emoji icons per type — shown on cards and list rows.
EMO = {
    "folder":"\U0001F4C1","image":"\U0001F5BC","video":"\U0001F3AC","audio":"\U0001F3B5",
    "document":"\U0001F4C4","code":"\U0001F4BB","data":"\U0001F4CA",
    "archive":"\U0001F5DC","file":"\U0001F4C4",
}

# Extensions served as text/plain for inline text preview.
# Binary files (zip, xlsx, etc.) are excluded intentionally.
TEXT_EXTS = {
    ".txt",".md",".py",".js",".ts",".jsx",".tsx",".html",".css",".json",
    ".xml",".yaml",".yml",".toml",".ini",".sh",".bash",".zsh",".rb",".go",
    ".rs",".c",".cpp",".h",".java",".kt",".swift",".php",".sql",".csv",
    ".env",".log",".conf",".cfg",".r",".vue",".dockerfile",".gitignore",
}

# Whitelist of files we serve from our own static/ directory.
# Prevents any other file from being accidentally exposed.
STATIC_FILES = {"style.css", "app.js"}

# Maximum bytes sent for text file preview.
# Prevents large log files from crashing the browser.
PREVIEW_LIMIT = 102400  # 100 KB


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_type(ext):
    """Return the category name for a given file extension."""
    for t, s in TYPE_MAP.items():
        if ext.lower() in s: return t
    return "file"


def fmt_size(b):
    """Format a byte count into a human-readable string (e.g. 1.2 MB)."""
    if b == 0: return ""
    for u in ["B","KB","MB","GB"]:
        if b < 1024: return f"{int(b)} {u}" if u == "B" else f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"


def get_items(directory, url_path):
    """
    Scan a directory and return a list of dicts describing each entry.
    Hidden files (starting with .) are excluded.
    Folders are sorted before files; both groups sorted alphabetically.
    """
    items = []
    try:
        entries = sorted(
            os.scandir(directory),
            key=lambda e: (not e.is_dir(), e.name.lower())
        )
        for entry in entries:
            if entry.name.startswith("."): continue
            is_dir = entry.is_dir(follow_symlinks=False)
            ext    = "" if is_dir else os.path.splitext(entry.name)[1].lower()
            ftype  = "folder" if is_dir else get_type(ext)
            try:
                stat = entry.stat()
                size = 0 if is_dir else stat.st_size
                mod  = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            except Exception:
                size, mod = 0, ""
            # Build the URL for this entry relative to the root
            url = url_path.rstrip("/") + "/" + entry.name + ("/" if is_dir else "")
            items.append({
                "name": entry.name, "type": ftype, "ext": ext,
                "size": size, "size_str": fmt_size(size), "modified": mod,
                "url": url, "is_dir": is_dir,
                "icon": EMO.get(ftype, "\U0001F4C4"),
                "color": COLORS.get(ftype, "#94a3b8"),
            })
    except Exception:
        pass
    return items


def build_breadcrumb(url_path, root_name):
    """
    Build breadcrumb HTML links from the current URL path.
    Root is always shown as a link. Last segment is plain text (current location).
    """
    parts = [p for p in url_path.strip("/").split("/") if p]
    bits  = [f'<a href="/" class="cr">\U0001F3E0 {root_name}</a>']
    for i, p in enumerate(parts):
        href = "/" + "/".join(parts[:i+1]) + "/"
        if i == len(parts)-1: bits.append(f'<span class="cc">{p}</span>')
        else:                  bits.append(f'<a href="{href}" class="cr">{p}</a>')
    return '<span class="cs">&#8250;</span>'.join(bits)


def generate_html(directory, url_path, root_dir):
    """
    Build the full HTML page for a directory listing.
    Reads templates/index.html and replaces __PLACEHOLDER__ markers with
    real data. Returns a plain HTML string ready to send to the browser.
    """
    items      = get_items(directory, url_path)
    root_name  = os.path.basename(root_dir.rstrip("/")) or root_dir
    title      = os.path.basename(directory.rstrip("/")) or root_name
    breadcrumb = build_breadcrumb(url_path, root_name)
    total_sz   = fmt_size(sum(i["size"] for i in items if not i["is_dir"])) or "0 B"
    n_folders  = sum(1 for i in items if i["is_dir"])
    n_files    = sum(1 for i in items if not i["is_dir"])
    items_json = json.dumps(items, ensure_ascii=False)
    try:
        tmpl = open(
            os.path.join(PKG_DIR, "templates", "index.html"), encoding="utf-8"
        ).read()
    except FileNotFoundError:
        return "<h1>Error: templates/index.html not found. Reinstall the package.</h1>"
    return (tmpl
        .replace("__TITLE__",      title)
        .replace("__BREADCRUMB__", breadcrumb)
        .replace("__TOTAL_SIZE__", total_sz)
        .replace("__N_FOLDERS__",  str(n_folders))
        .replace("__N_FILES__",    str(n_files))
        .replace("__N_TOTAL__",    str(n_folders + n_files))
        .replace("__ITEMS_JSON__", items_json))


# ── HTTP Handler ──────────────────────────────────────────────────────────────

class FileServerHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom HTTP handler extending Python's SimpleHTTPRequestHandler.

    Route map:
      /static/<name>   → serve package CSS/JS from global_directory/static/
      /preview/<path>  → serve file inline for browser preview (no download header)
      everything else  → default SimpleHTTPRequestHandler behaviour
                         (serves files from root_dir, calls list_directory for folders)
    """

    root_dir = None   # Set by run_server() before starting
    pkg_dir  = PKG_DIR

    def __init__(self, *args, **kwargs):
        # Tell SimpleHTTPRequestHandler to serve files from root_dir.
        super().__init__(*args, directory=self.__class__.root_dir, **kwargs)

    def do_GET(self):
        """Route incoming GET requests."""
        if self.path.startswith("/static/"):
            self._serve_pkg_static()
        elif self.path.startswith("/preview/"):
            self._serve_preview()
        else:
            super().do_GET()

    def _serve_pkg_static(self):
        """
        Serve CSS/JS from the package's own static/ directory.
        Only files in STATIC_FILES whitelist are allowed — prevents
        accidentally exposing other package internals.
        """
        name = self.path[len("/static/"):]
        if name not in STATIC_FILES:
            self.send_error(404); return
        path = os.path.join(self.__class__.pkg_dir, "static", name)
        if not os.path.isfile(path):
            self.send_error(404); return
        mime, _ = mimetypes.guess_type(path)
        data = open(path, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", mime or "text/plain")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _serve_preview(self):
        """
        Serve a file inline for browser preview (no Content-Disposition: attachment).
        Security: realpath check ensures the resolved path stays within root_dir.
        Text files: served as text/plain so browser renders them, capped at PREVIEW_LIMIT.
        Binary files (images, audio, video, PDF): served in full with correct MIME type.
        """
        url_path  = self.path[len("/preview"):]
        file_path = os.path.realpath(
            os.path.join(self.__class__.root_dir, url_path.lstrip("/")))
        root = self.__class__.root_dir
        # Path traversal check — must be inside root_dir
        if not (file_path == root or file_path.startswith(root + os.sep)):
            self.send_error(403); return
        if not os.path.isfile(file_path):
            self.send_error(404); return
        ext  = os.path.splitext(file_path)[1].lower()
        mime, _ = mimetypes.guess_type(file_path)
        if ext in TEXT_EXTS:
            mime = "text/plain; charset=utf-8"
        size = os.path.getsize(file_path)
        # Cap text previews at PREVIEW_LIMIT to protect the browser
        send_size = min(size, PREVIEW_LIMIT) if ext in TEXT_EXTS else size
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", send_size)
        self.end_headers()
        with open(file_path, "rb") as f:
            remaining = send_size
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk: break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def list_directory(self, path):
        """
        Override SimpleHTTPRequestHandler's default directory listing.
        Generates our custom HTML UI instead of the plain Python default.
        """
        url_path = unquote(urlparse(self.path).path)
        html     = generate_html(path, url_path, self.__class__.root_dir)
        data     = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        return io.BytesIO(data)

    def log_message(self, *args): pass   # Suppress default request logging
    def log_error(self, *args):   pass   # Suppress default error logging


# ── Entry point ───────────────────────────────────────────────────────────────

def run_server(directory, port):
    """Start the HTTP server. Called from cli.py in a daemon thread."""
    FileServerHandler.root_dir = os.path.realpath(directory)
    server = http.server.HTTPServer(("127.0.0.1", port), FileServerHandler)
    server.serve_forever()
