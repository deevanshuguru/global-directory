[![PyPI](https://img.shields.io/pypi/v/global-directory)](https://pypi.org/project/global-directory/) [![PyPI Downloads](https://img.shields.io/pypi/dm/global-directory)](https://pypi.org/project/global-directory/)

# global-directory

**Share files from your computer for free. One command. Anyone gets a link.**

No account. No upload. No cost. Files stay on your machine — just a public link anyone can open from any device.

---

## How simple is it?

    cd /your/folder
    global-directory start

That is it. A public link and QR code appear in your terminal. Share either one. Stop anytime.

---

## Why people use it

| You want to...                    | Old way                                    | With global-directory            |
|-----------------------------------|--------------------------------------------|----------------------------------|
| Share files with a client         | Upload to cloud, set permissions, send link | One command, instant link        |
| Send a large video or folder      | Too big for email, slow to upload           | No size limits, works instantly  |
| Share a project with a teammate   | Zip it, upload it, wait                    | Public link in seconds           |
| Show files during a meeting       | Screen share only                          | QR code — anyone scans and opens |
| Share from Mac to Android         | Platform tools won't connect               | Link opens on any device         |
| Give someone temporary access     | Cloud accounts, permissions, storage       | Start, share, stop when done     |

---

## Why it is different

- **Free** — no cost, ever
- **No account** — nothing to sign up for
- **No upload** — files served directly from your machine, nothing stored in cloud
- **One command** — literally just one
- **Any device** — phone, laptop, tablet, any OS, any browser
- **Full control** — Ctrl+C stops sharing instantly, link dies immediately

---

## Install

    pip install global-directory

Then install the free connector (one time only):

    Mac      →  brew install cloudflared
    Linux    →  https://github.com/cloudflare/cloudflared/releases
    Windows  →  winget install Cloudflare.cloudflared

No Cloudflare account needed.

---

## Usage

    cd /folder/you/want/to/share
    global-directory start

A public link and QR code appear. Share either one.

To stop:

    global-directory stop

---

## How it works

1. Starts a local file server on your machine
2. Opens a free Cloudflare quick tunnel
3. Prints a public link and QR code in your terminal
4. Anyone with the link can browse and download your files

---

## What people see

A clean file browser — grid or list view, search by name, filter by file type, sort by name or size, navigate into subfolders, download anything.

---

## Limitations

- Free quick tunnels support up to 200 simultaneous connections
- Traffic routes through Cloudflare infrastructure — do not share confidential files
- Windows: cloudflared does not auto-update — check github.com/cloudflare/cloudflared for updates

---

## GitHub

https://github.com/deevanshuguru/global-directory
