# Cloudflare Tunnel for InsightIQ

This directory contains the Cloudflare Tunnel integration for hosting InsightIQ live over the internet with zero port forwarding and free SSL/TLS encryption.

## Files

- `cloudflared.exe` - Official Cloudflare Tunnel client binary for Windows (x64).
- `run_tunnel.ps1` - PowerShell script that starts the tunnel, captures the public URL (`https://*.trycloudflare.com`), displays it in the console, and launches your browser.

## How to Run

Simply run **`ANSH.bat`** in the project root.

`ANSH.bat` will automatically:
1. Start the FastAPI backend server on `http://localhost:8000`.
2. Start the Vite React frontend server on `http://localhost:3000`.
3. Start the Cloudflare Tunnel targeting `http://localhost:3000`.
4. Capture the generated live HTTPS URL (e.g., `https://random-words.trycloudflare.com`).
5. Open the live URL automatically in your default browser.

## Security & Architecture

- **Single Tunnel Ingress**: The Cloudflare Tunnel connects directly to Vite on port 3000.
- **Reverse Proxy**: Vite automatically proxies all `/api/*` endpoints to the FastAPI backend on port 8000.
- **Zero Port Forwarding**: Traffic is routed securely through Cloudflare's Edge network over outbound TLS/QUIC connections.
- **CORS Configured**: FastAPI is configured to accept requests from both local development servers and Cloudflare Tunnel origins.
