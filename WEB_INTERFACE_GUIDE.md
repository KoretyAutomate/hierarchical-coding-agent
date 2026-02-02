# Coding Agent Web Interface - Setup Guide

## 🎉 Your Private Web Interface is Ready!

Access the coding agent from your mobile or any browser with a secure, authenticated interface.

## 📱 Access Information

### From Mobile (on same network):
```
http://192.168.1.161:8080
```

### From this computer:
```
http://localhost:8080
```

## 🔐 Login Credentials

**Current credentials:**
- Username: `admin`
- Password: `ZTEuxhFsataQy6k8dNvhCQ`

### Set Custom Credentials

Edit `/home/korety/coding-agent/.env` and add:
```bash
WEB_USERNAME=your_username
WEB_PASSWORD=your_secure_password
```

Then restart the interface.

## 🚀 Start/Stop the Interface

### Start:
```bash
cd ~/coding-agent
./start_web_interface.sh
```

### Start on custom port:
```bash
./start_web_interface.sh 9000
```

### Stop:
```bash
pkill -f "web_interface.py"
```

### Check if running:
```bash
ps aux | grep web_interface
```

## 📋 Features

- ✅ **Submit coding tasks** from your mobile
- ✅ **Monitor task status** in real-time (auto-refresh every 5 seconds)
- ✅ **View task history** (last 20 tasks)
- ✅ **Secure authentication** (username/password)
- ✅ **Mobile-responsive design** (works on all devices)
- ✅ **Private access** (only accessible with credentials)

## 🔒 Security Notes

1. **Network Access**: The interface binds to `0.0.0.0:8080`, meaning it's accessible from any device on your network
2. **Authentication**: Always required - no public access
3. **HTTPS**: For production use, consider setting up HTTPS with nginx
4. **Firewall**: Make sure only your devices can access the network

## 📖 How to Use

1. Open the URL on your mobile browser
2. Enter username and password
3. Type your coding task in the text area
4. Click "Submit Task"
5. Watch as the task progresses:
   - **Pending** (yellow) - Waiting to start
   - **In Progress** (blue) - Currently running
   - **Awaiting Approval** (orange) - Plan ready for review
   - **Completed** (green) - Task finished
   - **Failed** (red) - Error occurred

## 🛠️ Workflow

When you submit a task:

1. **Task Created** → Stored in database
2. **Plan Generation** → Qwen3-32B creates implementation plan
3. **Awaiting Approval** → Plan ready (you can view it via API)
4. **Implementation** → Qwen3-Coder implements the code
5. **Review** → Qwen3-32B reviews the implementation
6. **Testing** → Claude runs tests
7. **Completed** → Ready for PR

## 📊 Database

Tasks are stored in:
```
/home/korety/coding-agent/tasks.db
```

View tasks directly:
```bash
sqlite3 ~/coding-agent/tasks.db "SELECT * FROM tasks;"
```

## 🔧 Troubleshooting

### Can't access from mobile?
- Ensure your mobile is on the same network
- Check firewall settings: `sudo ufw allow 8080`
- Verify server is running: `ps aux | grep web_interface`

### Forgot password?
- Check logs: `cat ~/coding-agent/logs/web_interface.log`
- Or set new credentials in `.env` file

### Interface not responding?
- Check logs: `tail -f ~/coding-agent/logs/web_interface.log`
- Restart: `pkill -f web_interface.py && ./start_web_interface.sh`

## 📱 Mobile Browser Recommended Settings

- **Save to Home Screen** for app-like experience
- **Enable Auto-fill** for easy login
- **Bookmark the URL** for quick access

## 🎯 Next Steps

1. Save the login credentials securely
2. Bookmark the URL on your mobile
3. Try submitting a test task
4. Set custom credentials for better security

---

**Server IP**: 192.168.1.161
**Port**: 8080
**Status**: ✅ Running (PID: 731472)
