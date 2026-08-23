# ⚡ Quick Fix: Agent Not Joining Room

## The Problem

```
❌ Agent did not join the room
❌ signal connection failed: Timeout("transport timed out")
```

## Most Likely Cause

**Windows Firewall is blocking the LiveKit agent's WebSocket connection.**

---

## 🔧 Quick Fix (5 minutes)

### Option 1: Add Firewall Exception ⭐ RECOMMENDED

1. **Press Windows Key** and search **"Windows Defender Firewall"**
2. Click **"Allow an app through firewall"**
3. Click **"Change settings"** (requires admin)
4. Click **"Allow another app..."**
5. Browse to: `D:\voice_stream\backend\.venv\Scripts\python.exe`
6. **Check both** Private and Public
7. Click **OK**

### Option 2: Use Mobile Hotspot 📱

1. **Enable mobile hotspot** on your phone
2. **Connect your PC** to the hotspot
3. **Run the agent** again

This bypasses your home/office network firewall!

### Option 3: Disable Antivirus Temporarily

1. **Temporarily disable** your antivirus (Norton/McAfee/Avast/etc.)
2. **Run the agent**
3. If it works, **add exception** for the Python executable

---

## ✅ Test the Fix

```bash
cd backend
.venv\Scripts\activate

# Run diagnostic
python diagnose_connectivity.py

# Start agent
python -m app.agent.runner dev
```

### Expected Success Output:

```
✅ registered worker {"agent_name": "vyamit-voice"}
✅ received job request  
✅ session_started
```

---

## 🆘 Still Not Working?

### Check These:

1. **Are you behind a corporate VPN?**
   - Try disconnecting from VPN

2. **Running on corporate network?**
   - Contact IT to allow: `wss://vyamit-cpoa7nzp.livekit.cloud`

3. **Check Windows Firewall Rules:**
   ```powershell
   # Run in PowerShell as Admin
   Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Python*"}
   ```

4. **Test port 443 (WSS):**
   ```powershell
   Test-NetConnection -ComputerName vyamit-cpoa7nzp.livekit.cloud -Port 443
   ```
   Should show: `TcpTestSucceeded : True`

---

## 📋 Full Diagnostic

Run the automated fix script:

```bash
cd backend
fix_agent_connection.bat
```

This will:
- ✅ Test connectivity
- ✅ Verify credentials
- ✅ Test all providers
- ✅ Start the agent

---

## 🎯 Summary

| Issue | Solution |
|-------|----------|
| Firewall blocking | Add Python to firewall exceptions |
| Network restrictions | Use mobile hotspot |
| Antivirus blocking | Add exception or disable temporarily |
| Corporate network | Contact IT or use VPN |
| Slow connection | Use faster network |

---

## Success Checklist

After fixing, you should be able to:

- [x] Agent registers with LiveKit
- [x] Agent receives job requests
- [x] Agent joins room successfully
- [x] User can speak and hear responses
- [x] Automatic language switching works

---

## 🚀 Once Fixed

1. **Start backend**: `python -m app.agent.runner dev`
2. **Open Flutter app**
3. **Click "Connect to voice assistant"**
4. **Start speaking** in Hindi/Marathi/English
5. **Enjoy natural voice responses!** 🎤✨

---

**Need more help?** See detailed guide: `AGENT_NOT_JOINING_FIX.md`
