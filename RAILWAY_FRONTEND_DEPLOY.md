# Railway Frontend Deployment Guide

This guide walks you through adding the frontend service to your existing Railway project.

---

## Prerequisites

✅ Backend already deployed and working  
✅ PostgreSQL database connected  
✅ Backend URL: `https://www.jonesdatasoftware.com` (or your Railway backend URL)

---

## Step 1: Add Frontend Service to Railway

1. **Go to your Railway project** (same project as backend)
2. Click **"+ New"** → **"GitHub Repo"**
3. Select your repository: `Trading_Dashboard_AI`
4. Railway will detect the new service

**Important:** Railway needs to know which Dockerfile to use for the frontend.

---

## Step 2: Configure Frontend Service

### Option A: Using Railway Dashboard

1. Go to the **frontend service** settings
2. Click **"Settings"** → **"Build"**
3. Set **Root Directory**: `apps/frontend`
4. Set **Dockerfile Path**: `apps/frontend/Dockerfile`

### Option B: Using railway.toml (Already Created)

The `apps/frontend/railway.toml` file is already configured:
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "apps/frontend/Dockerfile"

[deploy]
startCommand = "nginx -g 'daemon off;'"
healthcheckPath = "/health"
```

Railway will automatically detect this file.

---

## Step 3: Set Frontend Environment Variables

In the **frontend service** → **Variables** tab, add:

```
VITE_API_URL=https://www.jonesdatasoftware.com
```

**Replace** `https://www.jonesdatasoftware.com` with your actual backend Railway URL.

**Note:** This environment variable is used at **build time** by Vite, so it gets baked into the static files.

---

## Step 4: Deploy Frontend

### Manual Deploy (First Time)
1. In Railway dashboard, click **"Deploy"** on the frontend service
2. Watch the build logs
3. Wait for "Deployment successful"

### Automatic Deploy (After Setup)
- Pushes to `main` will trigger both backend and frontend deploys
- Railway detects changes in `apps/frontend/` and rebuilds automatically

---

## Step 5: Verify Frontend Deployment

1. **Get Frontend URL**
   - Go to frontend service → Settings → Domains
   - Railway provides a URL like: `https://your-frontend.up.railway.app`

2. **Test Health Endpoint**
   ```bash
   curl https://your-frontend.up.railway.app/health
   ```
   Should return: `healthy`

3. **Open in Browser**
   - Visit: `https://your-frontend.up.railway.app`
   - Should see the Trading Dashboard landing page

4. **Test Demo**
   - Click "View Creator Demo"
   - Should load metrics, chart, and AI insights from backend

---

## Step 6: Connect Custom Domain (Optional)

If you want to use a custom domain:

1. In frontend service → Settings → Domains
2. Click "Add Domain"
3. Enter your domain (e.g., `dashboard.jonesdatasoftware.com`)
4. Add the CNAME record to your DNS provider:
   ```
   CNAME dashboard -> your-frontend.up.railway.app
   ```
5. Railway automatically provisions SSL certificate

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│           Railway Project                       │
│                                                 │
│  ┌──────────────────┐    ┌──────────────────┐  │
│  │   Frontend       │    │   Backend        │  │
│  │   (Nginx)        │───▶│   (FastAPI)      │  │
│  │   Port 80        │    │   Port 8000      │  │
│  └──────────────────┘    └──────────────────┘  │
│                                   │             │
│                          ┌────────▼────────┐    │
│                          │   PostgreSQL    │    │
│                          │   Database      │    │
│                          └─────────────────┘    │
└─────────────────────────────────────────────────┘
```

**Frontend:**
- Serves static React build via Nginx
- Makes API calls to backend URL
- Handles routing with React Router

**Backend:**
- FastAPI REST API
- CORS enabled for frontend origin
- Connects to PostgreSQL

---

## Troubleshooting

### Issue: Frontend can't reach backend

**Symptoms:** API calls fail, CORS errors in browser console

**Fix:**
1. Verify `VITE_API_URL` is set correctly in frontend variables
2. Check backend CORS settings allow frontend origin
3. Rebuild frontend after changing `VITE_API_URL`

### Issue: 404 on React routes

**Symptoms:** Direct URLs like `/dashboard` return 404

**Fix:**
- The `nginx.conf` already handles this with `try_files`
- Verify `nginx.conf` was copied correctly in Dockerfile

### Issue: Build fails - npm install errors

**Symptoms:** "Cannot find module" or dependency errors

**Fix:**
1. Check `package-lock.json` is committed to Git
2. Verify Node version in Dockerfile matches development (20-alpine)
3. Try deleting `node_modules` locally and reinstalling

### Issue: Blank page after deployment

**Symptoms:** Frontend loads but shows blank screen

**Fix:**
1. Check browser console for errors
2. Verify `VITE_API_URL` is set correctly
3. Check backend is responding at the configured URL
4. Verify CORS headers in backend allow frontend origin

---

## Environment Variables Reference

| Variable | Required | Set Where | Example |
|----------|----------|-----------|---------|
| `VITE_API_URL` | Yes | Frontend service | `https://www.jonesdatasoftware.com` |

**Important:** `VITE_API_URL` is used at **build time**, not runtime. If you change it, you must redeploy the frontend.

---

## Cost Estimate

**Railway Pricing (Both Services):**
- Backend: ~$5-10/month
- Frontend: ~$3-5/month
- PostgreSQL: ~$5-10/month
- **Total:** ~$13-25/month on Hobby plan

---

## Next Steps After Deployment

1. ✅ Test all features end-to-end
2. ✅ Upload a CSV and verify P&L calculations
3. ✅ Test AI coach insights
4. ✅ Verify animations and chart rendering
5. ✅ Test on mobile devices
6. ✅ Set up custom domain (optional)
7. ✅ Configure monitoring/alerts

---

## Deployment Checklist

- [ ] Frontend Dockerfile created
- [ ] Nginx config created
- [ ] Frontend railway.toml created
- [ ] Frontend service added to Railway project
- [ ] `VITE_API_URL` environment variable set
- [ ] Frontend deployed successfully
- [ ] Health check passing
- [ ] Landing page loads
- [ ] Demo dashboard works
- [ ] CSV upload works
- [ ] Chart renders correctly
- [ ] AI insights load
- [ ] Mobile responsive

---

## Support

- Railway Docs: https://docs.railway.app
- PRD Reference: `LLM_PLAN/Product_Requirement_Document.md`
- Backend Guide: `RAILWAY_DEPLOY_GUIDE.md`
