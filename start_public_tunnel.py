import subprocess
import re
import sys
import os
import time

# Ensure UTF-8 output
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def start_tunnel():
    print("==========================================================")
    print("🚀 Connecting StatSkill AI to Public Mobile Network...")
    print("==========================================================")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cloudflared_exe = os.path.join(current_dir, "cloudflared.exe")
    
    if not os.path.exists(cloudflared_exe):
        print(f"[ERROR] cloudflared.exe not found at {cloudflared_exe}")
        return

    # Run cloudflared with dynamic metrics port to avoid conflicts
    process = subprocess.Popen(
        [cloudflared_exe, "tunnel", "--url", "http://localhost:8000", "--metrics", "127.0.0.1:0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    url_found = False
    try:
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if not url_found:
                # Search specifically for the full HTTPS URL
                match = re.search(r"(https://[a-zA-Z0-9-]+\.trycloudflare\.com)", line)
                if match:
                    tunnel_url = match.group(1)
                    url_found = True
                    print("\n" + "="*70)
                    print("🎉 SUCCESS! YOUR APP IS NOW ACCESSIBLE ON ANY PHONE / DEVICE:")
                    print(f"👉 LINK: {tunnel_url}")
                    print("="*70)
                    print("(Keep this window open while testing on your phone)\n")
            
            # Print connection status updates
            if "Registered tunnel connection" in line or "location=" in line:
                print(f"[STATUS] Connected to Cloudflare Edge Network.")
    except KeyboardInterrupt:
        print("\nStopping tunnel...")
        process.terminate()

if __name__ == "__main__":
    start_tunnel()
