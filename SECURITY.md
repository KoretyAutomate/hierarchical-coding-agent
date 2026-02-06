# Security Configuration Guide

## HTTPS Setup (Recommended for Production)

### Option 1: Reverse Proxy with Nginx

1. Install nginx and certbot:
```bash
sudo apt install nginx certbot python3-certbot-nginx
```

2. Configure nginx (`/etc/nginx/sites-available/coding-agent`):
```nginx
server {
    listen 80;
    server_name your-dgx-ip-or-domain;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name your-dgx-ip-or-domain;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

3. Enable site and get SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/coding-agent /etc/nginx/sites-enabled/
sudo certbot --nginx -d your-domain
sudo systemctl restart nginx
```

### Option 2: Uvicorn with SSL

1. Generate self-signed certificate (for testing):
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

2. Update start script:
```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8080,
    ssl_keyfile="key.pem",
    ssl_certfile="cert.pem"
)
```

## Environment Variables

Set strong credentials:
```bash
export WEB_USERNAME="your_secure_username"
export WEB_PASSWORD="your_secure_password_min_16_chars"
```

Add to `~/.bashrc` for persistence:
```bash
echo 'export WEB_USERNAME="your_secure_username"' >> ~/.bashrc
echo 'export WEB_PASSWORD="your_secure_password_min_16_chars"' >> ~/.bashrc
source ~/.bashrc
```

## Network Security

### Firewall Configuration
```bash
# Allow only specific IPs
sudo ufw allow from YOUR_PHONE_IP to any port 8080
sudo ufw enable

# Check status
sudo ufw status
```

### IP Whitelist (in code)
Add to web_interface.py after app initialization:
```python
ALLOWED_IPS = ["192.168.1.100", "10.0.0.50"]  # Your phone IPs

@app.middleware("http")
async def ip_whitelist(request: Request, call_next):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        return JSONResponse(
            status_code=403,
            content={"detail": "Access denied"}
        )
    return await call_next(request)
```

## Best Practices

1. **Use HTTPS** - Never use HTTP for production
2. **Strong passwords** - Min 16 characters, mix of letters/numbers/symbols
3. **Limit access** - Use firewall/IP whitelist
4. **Regular updates** - Keep dependencies updated
5. **Monitor logs** - Check for suspicious activity
6. **Backup data** - Regular database backups

## Quick Start Commands

### Start with custom credentials
```bash
cd /home/korety/coding-agent
export WEB_USERNAME="myuser"
export WEB_PASSWORD="mysecurepassword123"
python3 web_interface.py 8080
```

### Start as systemd service (auto-restart)
Create `/etc/systemd/system/coding-agent-web.service`:
```ini
[Unit]
Description=Coding Agent Web Interface
After=network.target

[Service]
Type=simple
User=korety
WorkingDirectory=/home/korety/coding-agent
Environment="WEB_USERNAME=your_username"
Environment="WEB_PASSWORD=your_password"
ExecStart=/usr/bin/python3 /home/korety/coding-agent/web_interface.py 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable coding-agent-web
sudo systemctl start coding-agent-web
sudo systemctl status coding-agent-web
```

## Troubleshooting

### Check if port is in use
```bash
sudo lsof -i :8080
```

### View logs
```bash
# If running as systemd service
sudo journalctl -u coding-agent-web -f

# If running manually
# Check terminal output
```

### Test connection
```bash
# From DGX
curl http://localhost:8080

# From phone (replace with your DGX IP)
curl http://192.168.1.100:8080
```

## Security Checklist

- [ ] HTTPS enabled
- [ ] Strong credentials set
- [ ] Firewall configured
- [ ] IP whitelist enabled (optional)
- [ ] Regular backups scheduled
- [ ] Monitoring enabled
- [ ] Default credentials changed
- [ ] Dependencies up to date
