# Cloudflare Tunnel for InsightIQ

This directory contains the Cloudflare Tunnel integration for hosting InsightIQ live over the internet with zero port forwarding and free SSL/TLS encryption.

## Files

- `cloudflared.exe` - Official Cloudflare Tunnel client binary for Windows (x64).
- `run_tunnel.ps1` - PowerShell script that starts the tunnel, waits for local frontend/backend readiness, verifies global DNS propagation and HTTPS connectivity, and launches the browser.

## How to Run

Simply run **`ANSH.bat`** in the project root.

`ANSH.bat` executes the full launch pipeline:
1. Cleans up any prior orphaned tunnel processes and flushes local DNS cache.
2. Starts the FastAPI backend server on `http://localhost:8000`.
3. Starts the Vite React frontend server on `http://localhost:3000`.
4. Starts Cloudflare Tunnel targeting `http://localhost:3000`.
5. Verifies global DNS resolution for the newly assigned subdomain.
6. Verifies end-to-end HTTPS connectivity (HTTP 200 OK) before opening your browser.

## Troubleshooting: "DNS_PROBE_POSSIBLE" or "This site can't be reached"

Cloudflare Quick Tunnels generate a brand-new random subdomain (e.g. `xyz.trycloudflare.com`) on every launch.

Because the domain was just created seconds ago:
- **Global DNS Propagation**: Most worldwide DNS servers update within 5 to 15 seconds.
- **Local ISP DNS Cache**: If your local ISP router (such as JioFiber, Airtel, etc.) was queried before Cloudflare's record propagated, Chrome may temporarily display `DNS_PROBE_POSSIBLE`.

### Fixes:
1. **Wait 10 seconds and click 'Reload'** in Chrome. Once the DNS record reaches your ISP, the page loads immediately.
2. **Enable Secure DNS (DoH) in Chrome**:
   - Open Chrome Settings -> **Privacy and security** -> **Use secure DNS**.
   - Select **Cloudflare (1.1.1.1)** or **Google (Public DNS)**.
   - This bypasses slow ISP resolvers and resolves all Cloudflare tunnel domains instantly.
