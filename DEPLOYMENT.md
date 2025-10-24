# 🚀 Deployment Guide

This guide covers deploying the Trading Performance Dashboard to various platforms.

## Table of Contents
- [Railway.app (Recommended)](#railwayapp)
- [Render](#render)
- [Docker](#docker)
- [Manual Deployment](#manual-deployment)

---

## Railway.app

Railway is the recommended deployment platform for its simplicity and automatic deployments.

### Prerequisites
- Railway account (https://railway.app)
- Railway CLI installed: `npm install -g @railway/cli`

### Backend Deployment

1. **Login to Railway**
```bash
railway login
```

2. **Initialize Project**
```bash
cd backend
railway init
```

3. **Add Environment Variables**
```bash
railway variables set PORT=8000
railway variables set ENVIRONMENT=production
railway variables set CORS_ORIGINS=https://your-frontend-domain.railway.app
```

4. **Deploy**
```bash
railway up
```

5. **Get Backend URL**
```bash
railway domain
# Note this URL for frontend configuration
```

### Frontend Deployment

1. **Update API URL**
Edit `frontend/src/pages/Upload.jsx` and replace `http://localhost:8000` with your Railway backend URL.

2. **Initialize Frontend Project**
```bash
cd ../frontend
railway init
```

3. **Deploy**
```bash
npm run build
railway up
```

4. **Configure Domain**
```bash
railway domain
```

---

## Render

Render provides free hosting for web services and static sites.

### Backend Deployment

1. **Create New Web Service**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: trading-dashboard-backend
     - **Root Directory**: backend
     - **Environment**: Python 3.11
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Add Environment Variables**
   - `ENVIRONMENT=production`
   - `CORS_ORIGINS=https://your-frontend-domain.onrender.com`

3. **Deploy** - Render will automatically deploy on push

### Frontend Deployment

1. **Create New Static Site**
   - Click "New +" → "Static Site"
   - Connect repository
   - Configure:
     - **Name**: trading-dashboard-frontend
     - **Root Directory**: frontend
     - **Build Command**: `npm install && npm run build`
     - **Publish Directory**: dist

2. **Add Environment Variable**
   - `VITE_API_URL=https://your-backend.onrender.com`

3. **Update Frontend Code**
   - Replace hardcoded API URLs with `import.meta.env.VITE_API_URL`

---

## Docker

Deploy using Docker and Docker Compose for full control.

### Prerequisites
- Docker and Docker Compose installed

### Local Docker Deployment

1. **Build and Run**
```bash
docker-compose up --build
```

2. **Access Application**
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000

### Production Docker Deployment

1. **Build Images**
```bash
# Backend
cd backend
docker build -t trading-dashboard-backend:latest .

# Frontend
cd ../frontend
docker build -t trading-dashboard-frontend:latest .
```

2. **Push to Registry** (Docker Hub, AWS ECR, etc.)
```bash
docker tag trading-dashboard-backend:latest your-registry/trading-dashboard-backend:latest
docker push your-registry/trading-dashboard-backend:latest

docker tag trading-dashboard-frontend:latest your-registry/trading-dashboard-frontend:latest
docker push your-registry/trading-dashboard-frontend:latest
```

3. **Deploy to Server**
```bash
# On your server
docker pull your-registry/trading-dashboard-backend:latest
docker pull your-registry/trading-dashboard-frontend:latest

docker run -d -p 8000:8000 --name backend your-registry/trading-dashboard-backend:latest
docker run -d -p 80:5173 --name frontend your-registry/trading-dashboard-frontend:latest
```

---

## Manual Deployment

### Backend (VPS/Cloud Server)

1. **Install Dependencies**
```bash
sudo apt update
sudo apt install python3.11 python3-pip nginx
```

2. **Setup Application**
```bash
cd /var/www
git clone your-repo
cd windsurf-project/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Create Systemd Service**
```bash
sudo nano /etc/systemd/system/trading-dashboard.service
```

```ini
[Unit]
Description=Trading Dashboard API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/windsurf-project/backend
Environment="PATH=/var/www/windsurf-project/backend/venv/bin"
ExecStart=/var/www/windsurf-project/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

4. **Start Service**
```bash
sudo systemctl start trading-dashboard
sudo systemctl enable trading-dashboard
```

### Frontend (Static Hosting)

1. **Build Frontend**
```bash
cd frontend
npm install
npm run build
```

2. **Deploy to Nginx**
```bash
sudo cp -r dist/* /var/www/html/
```

3. **Configure Nginx**
```bash
sudo nano /etc/nginx/sites-available/trading-dashboard
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

4. **Enable Site**
```bash
sudo ln -s /etc/nginx/sites-available/trading-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Environment Variables

### Backend
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)
- `ENVIRONMENT` - production/development
- `CORS_ORIGINS` - Comma-separated allowed origins

### Frontend
- `VITE_API_URL` - Backend API URL

---

## SSL/HTTPS Setup

### Using Certbot (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl restart nginx
```

---

## Monitoring & Logs

### Backend Logs
```bash
# Systemd service
sudo journalctl -u trading-dashboard -f

# Docker
docker logs -f backend
```

### Frontend Logs
```bash
# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

---

## Troubleshooting

### CORS Issues
- Ensure `CORS_ORIGINS` includes your frontend domain
- Check browser console for specific CORS errors

### API Connection Failed
- Verify backend is running: `curl http://localhost:8000`
- Check firewall rules
- Verify environment variables

### Build Failures
- Clear caches: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node/Python versions match requirements

---

## Performance Optimization

### Backend
- Use Gunicorn with multiple workers:
  ```bash
  gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
  ```

### Frontend
- Enable Nginx gzip compression
- Configure caching headers
- Use CDN for static assets

---

## Backup & Recovery

### Database Backup (Phase 2)
```bash
pg_dump -U postgres trading_dashboard > backup.sql
```

### Application Backup
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz /var/www/windsurf-project
```

---

For additional support, refer to the main README.md or contact Jake Jones.
