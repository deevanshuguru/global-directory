[![PyPI](https://img.shields.io/pypi/v/global-directory)](https://pypi.org/project/global-directory/) [![Downloads](https://img.shields.io/pypi/dm/global-directory)](https://pypi.org/project/global-directory/) [![Python](https://img.shields.io/badge/python-3.8+-blue)](https://pypi.org/project/global-directory/) [![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/deevanshuguru/global-directory/blob/main/LICENSE) [![Stars](https://img.shields.io/github/stars/deevanshuguru/global-directory)](https://github.com/deevanshuguru/global-directory/stargazers)

# global-directory

**Share files from your computer for free. One command. Anyone gets a public link.**

No account. No upload. No cost. Files stay on your machine — just a public link anyone can open from any device.

![Terminal](https://github.com/user-attachments/assets/b5d33952-77a3-45c1-87c6-8a9753842147)

---

## Features

- **One command** to share any folder publicly
- **Preview files inline** — images, video, audio, PDF, code with syntax highlighting
- **Beautiful file browser** — grid and list view
- **Filter by type** — Images, Video, Audio, Docs, Code, Data, Archives
- **Search** by filename, **sort** by name, size or date
- **Extension chips** — see and filter by exact file extension
- **QR code** printed in terminal for instant mobile access
- **Breadcrumb navigation** — browse into subfolders
- **Free** — Cloudflare quick tunnels, no account needed
- Files **never leave your machine** — nothing is uploaded
- Works on **Mac, Linux, Windows**

---

## Install

    pip install global-directory

Install the free tunnel connector once:

    Mac      →  brew install cloudflared
    Linux    →  https://github.com/cloudflare/cloudflared/releases
    Windows  →  winget install Cloudflare.cloudflared

---

## Usage

    cd /any/folder/you/want/to/share
    global-directory start

A public URL and scannable QR code appear in your terminal. Share either one.
Press Ctrl+C or run the stop command to end the session.

    global-directory stop

---

## What it looks like

### File browser — grid view with filters and search

![File Browser](https://github.com/user-attachments/assets/2e1d731b-1e0a-4be2-b7a7-47c68795199c)

### Code preview with syntax highlighting

![Code Preview](https://github.com/user-attachments/assets/79fff755-1476-4b49-8c36-5c5914f59024)

### Image preview

![Image Preview](https://github.com/user-attachments/assets/1946df2e-eb82-42d7-911f-e0b98bea696c)

---

## Use cases

| You want to...                    | Without this                         | With global-directory              |
|-----------------------------------|--------------------------------------|------------------------------------|
| Share files with a client         | Upload to Drive, set perms, send link | One command, instant link          |
| Send a large video or folder      | Too big for email, slow to upload     | No size limits, works instantly    |
| Share a project with a teammate   | Zip it, upload it, wait               | Public link in seconds             |
| Show files during a meeting       | Screen share only                     | QR code — anyone opens on phone    |
| Share from Mac to Android         | AirDrop does not work cross-platform  | Link opens on any device           |
| Give temporary download access    | Cloud accounts, permissions, storage  | Start, share link, stop when done  |

---

## How it works

1. Starts a local file server on your machine
2. Opens a free Cloudflare quick tunnel (trycloudflare.com)
3. Prints a public URL and QR code in your terminal
4. Anyone with the link can browse and download — files never leave your machine

---

## Limitations

- Free quick tunnels support up to 200 simultaneous connections
- Traffic routes through Cloudflare infrastructure — do not share confidential files
- Windows: cloudflared does not auto-update — check [releases](https://github.com/cloudflare/cloudflared/releases) manually
- Text file preview is capped at 100 KB to protect the browser

---

## Contributing

Pull requests welcome. For major changes please open an issue first to discuss what you would like to change.

---

## License

MIT — free to use, modify and distribute.

---

Made with ❤️ by [Deevanshu Guru](https://www.linkedin.com/in/deevanshu-guru/) &nbsp;·&nbsp; [GitHub](https://github.com/deevanshuguru) &nbsp;·&nbsp; [Instagram](https://www.instagram.com/deevanshu_guru)
