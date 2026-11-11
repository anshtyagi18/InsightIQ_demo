$ErrorActionPreference = "SilentlyContinue"
$TunnelDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $TunnelDir
$CloudflaredExe = Join-Path $TunnelDir "cloudflared.exe"
$LogFile = Join-Path $TunnelDir "tunnel.log"

# Check if cloudflared.exe exists, if not download it
if (-not (Test-Path $CloudflaredExe)) {
    Write-Host "[*] cloudflared.exe not found in tunnel folder. Downloading official release..." -ForegroundColor Yellow
    $downloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $downloadUrl -OutFile $CloudflaredExe -UseBasicParsing
    if (-not (Test-Path $CloudflaredExe)) {
        Write-Host "[!] Failed to download cloudflared.exe. Please place it in $TunnelDir" -ForegroundColor Red
        Exit 1
    }
    Write-Host "[+] cloudflared.exe downloaded successfully!" -ForegroundColor Green
}

# Remove old log file
if (Test-Path $LogFile) {
    Remove-Item $LogFile -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                INSIGHTIQ - CLOUDFLARE SECURE TUNNEL" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "[*] Connecting local platform to Cloudflare edge..." -ForegroundColor Gray

# Start cloudflared process
$process = Start-Process -FilePath $CloudflaredExe -ArgumentList "tunnel --url http://localhost:3000 --logfile `"$LogFile`"" -PassThru -WindowStyle Hidden

# Poll for live URL
$tunnelUrl = $null
$maxRetries = 40
Write-Host "[*] Establishing secure HTTPS live link..." -ForegroundColor Yellow

for ($i = 0; $i -lt $maxRetries; $i++) {
    Start-Sleep -Milliseconds 800
    if (Test-Path $LogFile) {
        $logContent = Get-Content -Path $LogFile -Raw -ErrorAction SilentlyContinue
        if ($logContent -match '(https://[a-zA-Z0-9-]+\.trycloudflare\.com)') {
            $tunnelUrl = $matches[1]
            break
        }
    }
}

if ($tunnelUrl) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "   SUCCESS: CLOUDFLARE LIVE TUNNEL ESTABLISHED!" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "   >> LIVE PUBLIC URL : $tunnelUrl" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host "   >> LOCAL FRONTEND  : http://localhost:3000" -ForegroundColor Cyan
    Write-Host "   >> LOCAL BACKEND   : http://localhost:8000" -ForegroundColor Cyan
    Write-Host "   >> SECURITY        : End-to-End TLS Encryption via Cloudflare Edge" -ForegroundColor Gray
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "[*] Opening live link in default browser..." -ForegroundColor Yellow
    
    # Open URL in default browser
    Start-Process $tunnelUrl

    Write-Host ""
    Write-Host "[i] The tunnel is active. Share the Live Public URL with anyone to access your project!" -ForegroundColor Cyan
    Write-Host "[i] Keep this window open. Press [Ctrl+C] when you want to stop the tunnel." -ForegroundColor DarkGray
    Write-Host ""
    
    # Wait for process or clean exit
    try {
        $process.WaitForExit()
    } finally {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "[!] Could not obtain Cloudflare Tunnel URL within timeout." -ForegroundColor Red
    Write-Host "[i] Check log output below:" -ForegroundColor Yellow
    if (Test-Path $LogFile) {
        Get-Content $LogFile -Tail 20
    }
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
}
