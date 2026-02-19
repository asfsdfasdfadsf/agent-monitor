$payload = [Console]::In.ReadToEnd()
if ($payload.Trim().Length -eq 0) { exit 0 }
try {
    Invoke-WebRequest -Uri "http://localhost:7778/event" -Method Post -ContentType "application/json" -Body $payload -TimeoutSec 2 -UseBasicParsing | Out-Null
} catch {}
exit 0
