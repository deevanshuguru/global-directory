
import os, sys, re, time, signal, socket, threading, subprocess

PID_FILE = os.path.join(os.path.expanduser("~"), ".global_directory.pid")

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0)); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def print_qr(url):
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url); qr.make(fit=True)
        qr.print_ascii(invert=True)
    except Exception: pass

def start_cmd():
    directory = os.path.realpath(os.getcwd())
    port      = find_free_port()
    print(f"\n  Global Directory  v3.0.0")
    print(f"  {'-'*46}")
    print(f"  Folder  : {directory}")
    print(f"  Local   : http://localhost:{port}")
    print(f"  Getting Cloudflare URL...\n")

    from global_directory.server import run_server
    threading.Thread(target=run_server, args=(directory, port), daemon=True).start()
    time.sleep(0.5)

    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    except FileNotFoundError:
        print("  ERROR: cloudflared not found.")
        print("  Mac:   brew install cloudflared")
        print("  Linux: https://github.com/cloudflare/cloudflared/releases")
        print("  Win:   winget install Cloudflare.cloudflared")
        return

    with open(PID_FILE, "w") as f: f.write(str(os.getpid()))

    url = None
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None: break
        line = proc.stdout.readline()
        m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if m: url = m.group(0); break

    if not url:
        print("  ERROR: Could not get tunnel URL."); proc.terminate()
        try: os.remove(PID_FILE)
        except: pass
        return

    bar = "=" * max(len(url)+4, 52)
    print(f"  {bar}\n   {url}\n  {bar}\n")
    print_qr(url)
    print(f"\n  Local also at: http://localhost:{port}")
    print(f"  Ctrl+C to stop\n")

    try: proc.wait()
    except KeyboardInterrupt: print("\n  Stopped.")
    finally:
        proc.terminate()
        try: os.remove(PID_FILE)
        except: pass

def stop_cmd():
    if not os.path.exists(PID_FILE):
        print("  Not running."); return
    try:
        with open(PID_FILE) as f: pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM); print(f"  Stopped (PID {pid})")
    except ProcessLookupError: print("  Already stopped.")
    except Exception as e: print(f"  Error: {e}")
    try: os.remove(PID_FILE)
    except: pass

def main():
    cmds = {"start": start_cmd, "stop": stop_cmd}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print("Usage:\n  global-directory start\n  global-directory stop"); sys.exit(0)
    cmds[sys.argv[1]]()

if __name__ == "__main__": main()
