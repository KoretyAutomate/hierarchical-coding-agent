# Quick Start Checklist

## Pre-Flight Check ✈️

Use this checklist to verify the implementation before first use.

---

## 1. Installation Verification ✅

### Dependencies
```bash
cd /home/korety/coding-agent

# Check Python version (need 3.8+)
python3 --version

# Check installed packages
pip list | grep -E "(fastapi|uvicorn|websockets)"
```

Expected output:
```
Python 3.10+ (or 3.8+)
fastapi           0.104.0+
uvicorn           0.24.0+
websockets        12.0+
```

### Files Present
```bash
# Check all required files exist
ls -la web_interface.py
ls -la hierarchical_orchestrator.py
ls -la requirements.txt
ls -la SECURITY.md
ls -la WEB_INTERFACE_README.md
```

All should show file sizes > 0

---

## 2. Database Check ✅

### Verify Schema
```bash
sqlite3 tasks.db "PRAGMA table_info(tasks);" | wc -l
```

Expected: **20** (columns)

### Check New Columns
```bash
sqlite3 tasks.db "PRAGMA table_info(tasks);" | grep -E "(plan_approved|workflow_state|retry_count)"
```

Should show:
- plan_approved_at
- plan_approved_by
- workflow_state
- retry_count
- (etc.)

---

## 3. Code Verification ✅

### Syntax Check
```bash
python3 -m py_compile web_interface.py
echo $?
```

Expected: **0** (no errors)

### Import Test
```bash
python3 -c "
from web_interface import WorkflowManager, WorkflowCheckpoint
print('✓ Imports successful')
"
```

Expected: `✓ Imports successful`

---

## 4. Network Preparation 🌐

### Find Your IP
```bash
# Get all network interfaces
ip addr show | grep "inet " | grep -v 127.0.0.1

# Or simpler
hostname -I
```

Note your IP (e.g., `192.168.1.100`)

### Check Port Availability
```bash
# Make sure port 8080 is free
sudo lsof -i :8080
```

Expected: **No output** (port is free)

If occupied:
```bash
# Find what's using it
sudo lsof -i :8080

# Kill if needed (be careful!)
sudo kill <PID>
```

---

## 5. Credentials Setup 🔐

### Set Custom Credentials (Recommended)
```bash
# Add to current session
export WEB_USERNAME="your_username"
export WEB_PASSWORD="your_secure_password_123"

# Add to ~/.bashrc for persistence
echo 'export WEB_USERNAME="your_username"' >> ~/.bashrc
echo 'export WEB_PASSWORD="your_secure_password_123"' >> ~/.bashrc
source ~/.bashrc
```

### Or Use Auto-Generated (Less Secure)
If you don't set credentials, a random password will be generated on each start.

---

## 6. Firewall Configuration (Optional) 🛡️

### Allow Access from Phone
```bash
# Find your phone's IP (check phone's WiFi settings)
# Then allow access:
sudo ufw allow from YOUR_PHONE_IP to any port 8080

# Or allow from entire subnet
sudo ufw allow from 192.168.1.0/24 to any port 8080

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## 7. First Start 🚀

### Start Server
```bash
cd /home/korety/coding-agent
python3 web_interface.py 8080
```

### Verify Startup
Look for:
```
============================================================
WEB INTERFACE CREDENTIALS
============================================================
Username: admin
Password: <your_password>
...
============================================================

Starting web interface on http://0.0.0.0:8080
Access from your mobile at http://YOUR_IP:8080
```

**IMPORTANT**: Copy the password! You'll need it to login.

### Test Locally
Open new terminal:
```bash
curl http://localhost:8080
```

Should return HTML (not error)

---

## 8. Mobile Access Test 📱

### From Your Phone

1. **Open browser** (Chrome/Safari)

2. **Navigate to**:
   ```
   http://YOUR_DGX_IP:8080
   ```
   Replace YOUR_DGX_IP with IP from step 4

3. **Login** with credentials from step 7

4. **Should see**:
   - Header: "🤖 Coding Agent"
   - "Submit New Task" form
   - "Recent Tasks" section

### Troubleshooting Mobile Access

**Can't connect?**
```bash
# On DGX, check server is running
ps aux | grep web_interface

# Check firewall
sudo ufw status

# Try ping from phone
# In phone browser: http://YOUR_DGX_IP:8080/api/tasks
```

---

## 9. First Task Test 🧪

### Submit Test Task

1. **In phone browser**, enter:
   ```
   Create a hello world function
   ```

2. **Click "Submit Task"**

3. **Should see**:
   - Progress modal opens
   - WebSocket connection established
   - Real-time updates appear

### Monitor on Server
Server console should show:
```
INFO:     127.0.0.1:xxxxx - "POST /api/tasks HTTP/1.1" 200 OK
INFO:     127.0.0.1:xxxxx - "WebSocket /ws/tasks/1" [accepted]
✓ Hierarchical Orchestrator initialized
```

### Check Database
```bash
sqlite3 tasks.db "SELECT id, request, status FROM tasks;"
```

Should show:
```
1|Create a hello world function|planning
```

---

## 10. Approval Flow Test ✅

### Wait for Plan

After 30-60 seconds:
1. **Plan modal should appear** automatically
2. **Review the plan**
3. **Click "✓ Approve"**

### Monitor Progress
- Progress modal reappears
- Shows "Stage: implementing"
- Updates continue

### Wait for Implementation

After 1-5 minutes:
1. **Implementation modal should appear**
2. **Review all sections**:
   - Original Plan
   - Implementation Result
   - Lead Review
   - Verification
3. **Click "✓ Approve & Complete"**

### Verify Completion
Task list should update:
```
#1                    [COMPLETED]
Create a hello world function
2026-02-02 12:35:00
```

---

## 11. WebSocket Test 🔌

### Browser DevTools
1. **Open DevTools** (F12 on desktop, or Safari Developer menu)
2. **Go to Network tab**
3. **Filter**: WS (WebSocket)
4. **Submit a task**
5. **Should see**:
   - WebSocket connection established
   - Messages flowing (green arrows)
   - Events: task_started, stage_started, etc.

### Test Reconnection
1. **Start a task**
2. **Close progress modal** (X button)
3. **Click the task again** in task list
4. **Progress modal reopens** with current status

---

## 12. Error Handling Test ⚠️

### Test Plan Rejection
1. **Submit task**: "Add a new feature"
2. **Wait for plan modal**
3. **Click "✗ Reject"**
4. **Enter reason**: "Too complex"
5. **Verify**:
   - Modal closes
   - Task status: `plan_rejected`
   - Workflow stopped

### Check Error Details
```bash
sqlite3 tasks.db "SELECT id, status, plan_rejection_reason FROM tasks WHERE status='plan_rejected';"
```

---

## 13. Plan Edit Test ✏️

### Test Plan Revision
1. **Submit task**: "Create a utility function"
2. **Wait for plan modal**
3. **Click "✎ Request Changes"**
4. **Enter feedback**: "Add error handling"
5. **Click "📤 Submit Changes"**
6. **Wait ~30s**
7. **Revised plan appears** in same modal
8. **Click "✓ Approve"**

---

## 14. Implementation Retry Test 🔄

### Test Retry
1. **Complete a task** to implementation approval
2. **In implementation modal**, click "🔄 Retry"
3. **Verify**:
   - Progress modal appears
   - Status: "implementing"
   - Retry count incremented

### Check Retry Count
```bash
sqlite3 tasks.db "SELECT id, retry_count FROM tasks WHERE retry_count > 0;"
```

---

## 15. Performance Test 📊

### Load Test (Optional)
```bash
# Submit 5 tasks rapidly
for i in {1..5}; do
  curl -X POST http://localhost:8080/api/tasks \
    -H "Content-Type: application/json" \
    -u admin:YOUR_PASSWORD \
    -d '{"request":"Test task '$i'"}'
done
```

### Monitor
```bash
# Check database
sqlite3 tasks.db "SELECT id, status FROM tasks ORDER BY id DESC LIMIT 5;"

# Should see 5 tasks in various states
```

---

## 16. Security Verification 🔒

### Authentication Test
```bash
# Without credentials (should fail)
curl http://localhost:8080/api/tasks

# Should return 401 Unauthorized
```

### HTTPS Check (If Setup)
```bash
# If you configured HTTPS
curl https://your-domain.com

# Should return HTML (not certificate error)
```

---

## 17. Mobile Compatibility ✅

### Test On Different Devices
- [ ] iPhone (Safari)
- [ ] Android (Chrome)
- [ ] Tablet (iPad/Android)

### Test Features
- [ ] Task submission works
- [ ] Modals display correctly
- [ ] Buttons are touch-friendly
- [ ] WebSocket connects
- [ ] Real-time updates appear
- [ ] Approve/reject works

---

## 18. Backup Test 💾

### Create Backup
```bash
# Backup database
cp tasks.db tasks-$(date +%Y%m%d).db

# Verify backup
ls -lh tasks-*.db
```

### Test Restore
```bash
# Stop server (Ctrl+C)
# Restore from backup
cp tasks-20260202.db tasks.db
# Restart server
python3 web_interface.py 8080
```

---

## 19. Cleanup Test 🧹

### Remove Test Tasks
```bash
sqlite3 tasks.db "DELETE FROM tasks WHERE request LIKE 'Test task%';"
sqlite3 tasks.db "SELECT COUNT(*) FROM tasks;"
```

### Restart Clean
```bash
# Stop server
# Delete database
rm tasks.db
# Restart (creates fresh database)
python3 web_interface.py 8080
```

---

## 20. Production Readiness ✅

### Final Checklist
- [ ] HTTPS configured (see SECURITY.md)
- [ ] Strong credentials set (16+ chars)
- [ ] Firewall rules enabled
- [ ] Systemd service configured (optional)
- [ ] Backup script setup (optional)
- [ ] Monitoring enabled (optional)
- [ ] Phone tested successfully
- [ ] Documentation read

---

## Troubleshooting Guide

### Problem: Server won't start

**Check:**
```bash
# Port in use?
sudo lsof -i :8080

# Python version?
python3 --version

# Dependencies installed?
pip list | grep fastapi
```

**Solution:**
```bash
# Kill process on port 8080
sudo lsof -i :8080 | grep LISTEN | awk '{print $2}' | xargs kill

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Problem: Can't access from phone

**Check:**
```bash
# Server running?
ps aux | grep web_interface

# Correct IP?
hostname -I

# Firewall blocking?
sudo ufw status
```

**Solution:**
```bash
# Allow from phone IP
sudo ufw allow from PHONE_IP to any port 8080

# Or disable firewall temporarily
sudo ufw disable
```

---

### Problem: WebSocket not connecting

**Check:**
- Browser console for errors
- Network tab → WS filter
- Server logs for WebSocket messages

**Solution:**
- Refresh page
- Clear browser cache
- Check network stability

---

### Problem: Modals not appearing

**Check:**
- Task status in database
- Browser console for JS errors
- WebSocket connection status

**Solution:**
```bash
# Check task status
sqlite3 tasks.db "SELECT id, status FROM tasks ORDER BY id DESC LIMIT 1;"

# Should be "plan_awaiting_approval" or "implementation_awaiting_approval"
```

---

### Problem: Database errors

**Check:**
```bash
# Database integrity
sqlite3 tasks.db "PRAGMA integrity_check;"

# Should return "ok"
```

**Solution:**
```bash
# Backup and recreate
cp tasks.db tasks.db.broken
rm tasks.db
python3 web_interface.py 8080
```

---

## Success Criteria ✅

You're ready for production when:

- ✅ Server starts without errors
- ✅ Access from phone works
- ✅ Authentication works
- ✅ WebSocket connects
- ✅ Task submission works
- ✅ Plan approval works
- ✅ Implementation approval works
- ✅ Real-time updates appear
- ✅ Modals display correctly
- ✅ Database has 20 columns
- ✅ HTTPS configured (recommended)
- ✅ Strong credentials set
- ✅ Firewall configured

---

## Next Steps

1. **Read** WEB_INTERFACE_README.md for full documentation
2. **Review** SECURITY.md for production security
3. **Check** WORKFLOW_GUIDE.md for visual walkthrough
4. **Setup** systemd service for auto-restart
5. **Configure** regular backups
6. **Test** with real coding tasks
7. **Monitor** logs for issues

---

## Quick Reference

### Start Server
```bash
cd /home/korety/coding-agent
python3 web_interface.py 8080
```

### Check Status
```bash
# Server running?
ps aux | grep web_interface

# Database tasks
sqlite3 tasks.db "SELECT id, status FROM tasks ORDER BY id DESC LIMIT 10;"

# Server logs (if systemd)
sudo journalctl -u coding-agent-web -f
```

### Emergency Stop
```bash
# Ctrl+C (if running in terminal)
# Or:
pkill -f web_interface.py
```

---

**Checklist Complete!** 🎉

If all tests pass, you're ready to use the enhanced web interface from your phone!
