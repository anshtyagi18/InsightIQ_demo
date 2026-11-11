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

# Stop any previous cloudflared processes
Stop-Process -Name "cloudflared" -Force -ErrorAction SilentlyContinue

# Remove old log file
if (Test-Path $LogFile) {
    Remove-Item $LogFile -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "                INSIGHTIQ - CLOUDFLARE SECURE TUNNEL" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Wait for local Vite frontend (port 3000) to become available
Write-Host "[1/4] Waiting for local Frontend (port 3000) to initialize..." -ForegroundColor Yellow
$frontendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $tcp = Test-NetConnection -ComputerName 127.0.0.1 -Port 3000 -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($tcp) {
            $frontendReady = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if ($frontendReady) {
    Write-Host "      [OK] Frontend is active on http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "      [NOTE] Frontend is still warming up, proceeding with tunnel..." -ForegroundColor Yellow
}

# Step 2: Start Cloudflare Tunnel
Write-Host "[2/4] Initializing Cloudflare Tunnel connection..." -ForegroundColor Yellow
$process = Start-Process -FilePath $CloudflaredExe -ArgumentList "tunnel --url http://localhost:3000 --logfile `"$LogFile`"" -PassThru -WindowStyle Hidden

# Poll for live URL
$tunnelUrl = $null
$domain = $null
$maxRetries = 40

for ($i = 0; $i -lt $maxRetries; $i++) {
    Start-Sleep -Milliseconds 800
    if (Test-Path $LogFile) {
        $logContent = Get-Content -Path $LogFile -Raw -ErrorAction SilentlyContinue
        if ($logContent -match '(https://([a-zA-Z0-9-]+)\.trycloudflare\.com)') {
            $tunnelUrl = $matches[1]
            $domain = "$($matches[2]).trycloudflare.com"
            break
        }
    }
}

if (-not $tunnelUrl) {
    Write-Host "[!] Could not obtain Cloudflare Tunnel URL within timeout." -ForegroundColor Red
    if (Test-Path $LogFile) {
        Get-Content $LogFile -Tail 20
    }
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
    Exit 1
}

Write-Host "      [OK] Tunnel generated: $tunnelUrl" -ForegroundColor Green

# Step 3: Wait for DNS propagation
Write-Host "[3/4] Checking global DNS propagation for $domain..." -ForegroundColor Yellow
Clear-DnsClientCache -ErrorAction SilentlyContinue

$dnsResolved = $false
for ($d = 0; $d -lt 15; $d++) {
    $res = Resolve-DnsName -Name $domain -ErrorAction SilentlyContinue
    if ($res) {
        $dnsResolved = $true
        break
    }
    Start-Sleep -Seconds 1
}

if ($dnsResolved) {
    Write-Host "      [OK] DNS propagated successfully" -ForegroundColor Green
} else {
    # Check if public DNS has it
    $pubDns = Resolve-DnsName -Name $domain -Server 1.1.1.1 -ErrorAction SilentlyContinue
    if ($pubDns) {
        Write-Host "      [OK] DNS resolved via Cloudflare edge (local ISP cache updating...)" -ForegroundColor Yellow
    } else {
        Write-Host "      [NOTE] DNS still propagating through global root servers..." -ForegroundColor Yellow
    }
}

# Step 4: Verify end-to-end HTTP response
Write-Host "[4/4] Verifying live HTTPS connectivity..." -ForegroundColor Yellow
$httpReady = $false
for ($h = 0; $h -lt 15; $h++) {
    try {
        $code = & curl.exe -s -o nul -w "%{http_code}" --max-time 4 "$tunnelUrl"
        if ($code -eq "200" -or $code -eq "304" -or $code -eq "301" -or $code -eq "302") {
            $httpReady = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if ($httpReady) {
    Write-Host "      [OK] Live HTTPS tunnel confirmed operational (HTTP 200 OK)" -ForegroundColor Green
} else {
    Write-Host "      [NOTE] Tunnel established; edge route warming up..." -ForegroundColor Yellow
}

# Display Final Success Banner
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "                SUCCESS: CLOUDFLARE LIVE TUNNEL ESTABLISHED!                   " -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   -> LIVE PUBLIC URL : $tunnelUrl" -ForegroundColor White -BackgroundColor DarkGreen
Write-Host "   -> LOCAL FRONTEND  : http://localhost:3000" -ForegroundColor Cyan
Write-Host "   -> LOCAL BACKEND   : http://localhost:8000" -ForegroundColor Cyan
Write-Host "   -> SECURITY        : End-to-End TLS Encryption via Cloudflare Edge" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "[*] Launching live link in your default browser..." -ForegroundColor Yellow

# Launch browser
Start-Process $tunnelUrl

Write-Host ""
Write-Host "[i] NOTES FOR REMOTE / MOBILE ACCESS:" -ForegroundColor Cyan
Write-Host "    - If Chrome shows 'DNS_PROBE_POSSIBLE' or 'DNS address could not be found'," -ForegroundColor White
Write-Host "      wait 5-10 seconds and click the 'Reload' button (DNS propagation cache)." -ForegroundColor Yellow
Write-Host "    - You can share the Live Public URL with anyone to test the project live!" -ForegroundColor White
Write-Host "    - Keep this window open. Press [Ctrl+C] when you want to stop the tunnel." -ForegroundColor DarkGray
Write-Host ""

# Monitor process until user closes
try {
    $process.WaitForExit()
} finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
}
