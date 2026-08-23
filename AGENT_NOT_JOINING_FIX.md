# Fix: Agent Not Joining Room

## Problem Analysis

From your logs, the agent is failing to join the room with these errors:

```
❌ signal connection failed on v1 path: Timeout("transport timed out")
❌ failed to connect: Signal(Timeout("transport timed out")), retrying...
❌ The room connection was not established within 10 seconds
```

## Root Causes

### 1. **Network/Firewall Issue** (Most Likely)
- The agent cannot establish WebSocket connection to LiveKit Cloud
- Connection timeout suggests network/firewall blocking

### 2. **Slow Network Latency**
- Log shows: `turn detection transport latency is too high: 1486ms`
- High latency causing timeouts

### 3. **Windows Firewall/Antivirus**
- May be blocking outgoing WebSocket connections

---

## Solutions

### Solution 1: Allow LiveKit Through Windows Firewall ⭐ RECOMMENDED

Run PowerShell as Administrator:

```powershell
# Allow Python through firewall
New-NetFirewallRule -DisplayName "Python LiveKit Agent" -Direction Outbound -Program "C:\Users\LOQ\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -Action Allow

# Allow your venv Python
New-NetFirewallRule -DisplayName "Python Venv LiveKit" -Direction Outbound -Program "D:\voice_stream\backend\.venv\Scripts\python.exe" -Action Allow
```

Or manually:
1. Windows Settings → Privacy & Security → Windows Security → Firewall
2. Click "Allow an app through firewall"
3. Add Python.exe from `.venv\Scripts\python.exe`
4. Enable both Private and Public networks

### Solution 2: Check Antivirus

If you're using antivirus software (Norton, McAfee, Avast, etc.):

1. **Temporarily disable** it
2. **Try running the agent** again
3. If it works, **add exception** for:
   - `D:\voice_stream\backend\.venv\Scripts\python.exe`
   - `wss://vyamit-cpoa7nzp.livekit.cloud`

### Solution 3: Use Different Network

Try running from:
- **Mobile hotspot** (bypasses corporate/home firewall)
- **Different WiFi network**
- **VPN** (if you have one)

### Solution 4: Increase Timeout Settings

Edit `backend/app/agent/runner.py` and add longer timeouts:

```python
# Around line 65-75, in the session configuration
await session.start(
    agent=VyamitAssistant(),
    room=ctx.room,
    room_options=room_options,
)
await ctx.connect(timeout=30.0)  # Add timeout parameter
```

### Solution 5: Check VPN/Proxy

If you're behind a corporate VPN or proxy:

```powershell
# Check proxy settings
echo $env:HTTP_PROXY
echo $env:HTTPS_PROXY

# Temporarily unset if present
$env:HTTP_PROXY=""
$env:HTTPS_PROXY=""

# Then try running agent again
```

---

## Quick Test Commands

### 1. Test Basic Connectivity
```bash
cd backend
.venv\Scripts\activate
python diagnose_connectivity.py
```

### 2. Test LiveKit Connection
```bash
# Simple curl test
curl -v https://vyamit-cpoa7nzp.livekit.cloud
```

### 3. Check if Port 443 is Open
```powershell
Test-NetConnection -ComputerName vyamit-cpoa7nzp.livekit.cloud -Port 443
```

Expected output:
```
TcpTestSucceeded : True
```

---

## Verify Agent Configuration

Check your `.env` file has correct credentials:

```env
LIVEKIT_URL=wss://vyamit-cpoa7nzp.livekit.cloud
LIVEKIT_API_KEY=APIZRsZ7yPoYdj3
LIVEKIT_API_SECRET=o2SbyteldvyloEAgAQX7efNj2243m0Jydg5YeJe6IxXC
```

### Test Credentials
```bash
cd backend
.venv\Scripts\activate
python -c "from app.config.settings import get_settings; s = get_settings(); print('✅ URL:', s.livekit_url); print('✅ Key:', s.livekit_api_key.get_secret_value() if s.livekit_api_key else 'None'); print('✅ Secret:', '***' if s.livekit_api_secret else 'None')"
```

---

## Alternative: Use Local LiveKit Server

If firewall issues persist, you can run LiveKit locally:

### Install LiveKit Server (Local)

```powershell
# Download LiveKit server
# https://github.com/livekit/livekit/releases

# Or use Docker
docker run --rm -p 7880:7880 -p 7881:7881 -p 7882:7882/udp livekit/livekit-server --dev
```

### Update `.env` for Local Server

```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

---

## Debugging Steps

### 1. Enable Verbose Logging

Add to `backend/app/core/logging.py`:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. Check Agent Process

```powershell
# See if agent is running
Get-Process python

# Check network connections
netstat -ano | findstr "443"
```

### 3. Monitor Network Traffic

Use Wireshark or Fiddler to see if packets are reaching LiveKit server.

---

## Working Configuration Example

Here's a tested working setup:

**`.env`:**
```env
LIVEKIT_URL=wss://your-instance.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
AGENT_NAME=vyamit-voice
```

**Start Agent:**
```bash
cd backend
.venv\Scripts\activate
python -m app.agent.runner dev
```

**Expected Output:**
```
✅ registered worker {"agent_name": "vyamit-voice"}
✅ received job request {"room": "..."}
✅ session_started room=...
```

---

## Common Error Messages & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `transport timed out` | Network/Firewall | Allow through firewall |
| `Audio Timeout Error` | No audio flowing | Normal - agent waiting for user |
| `turn detection transport latency is too high` | Slow network | Use faster connection |
| `failed to fetch region urls` | DNS/Network | Check internet |

---

## Still Not Working?

### Last Resort Options:

1. **Use ngrok tunnel** (bypass firewall):
   ```bash
   ngrok http 7880
   # Use ngrok URL in LIVEKIT_URL
   ```

2. **Contact your IT department**:
   - Request to whitelist: `*.livekit.cloud`
   - Port 443 (WSS) outbound
   - WebSocket protocol

3. **Check LiveKit Status**:
   - Visit: https://status.livekit.io
   - Verify no outages

4. **Update LiveKit SDK**:
   ```bash
   pip install --upgrade livekit livekit-agents
   ```

---

## Success Checklist

After fixing, you should see:

```
✅ registered worker
✅ received job request  
✅ session_started
✅ agent connected to room
✅ STT stream initialized
✅ User can speak and get responses
```

---

## Next Steps

1. ✅ Run `python diagnose_connectivity.py`
2. ✅ Add firewall exception for Python
3. ✅ Disable antivirus temporarily
4. ✅ Try mobile hotspot
5. ✅ Run agent: `python -m app.agent.runner dev`
6. ✅ Test from Flutter app

---

## Support

If none of these work, the issue is likely:
- **Corporate network** restricting WebSocket
- **ISP blocking** certain protocols  
- **Regional firewall** (some countries block certain cloud services)

**Best solution**: Use mobile hotspot to bypass network restrictions.
